/* 
 * MarkerManager, v1.0
 * Copyright (c) 2007 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. 
 *
 *
 * Author: Doug Ricket, others
 * 
 * Marker manager is an interface between the map and the user, designed
 * to manage adding and removing many points when the viewport changes.
 *
 *
 * Algorithm: The MM places its markers onto a grid, similar to the map tiles.
 * When the user moves the viewport, the MM computes which grid cells have
 * entered or left the viewport, and shows or hides all the markers in those
 * cells.
 * (If the users scrolls the viewport beyond the markers that are loaded,
 * no markers will be visible until the EVENT_moveend triggers an update.)
 *
 * In practical consequences, this allows 10,000 markers to be distributed over
 * a large area, and as long as only 100-200 are visible in any given viewport,
 * the user will see good performance corresponding to the 100 visible markers,
 * rather than poor performance corresponding to the total 10,000 markers.
 *
 * Note that some code is optimized for speed over space,
 * with the goal of accommodating thousands of markers.
 *
 */



/**
 * Creates a new MarkerManager that will show/hide markers on a map.
 *
 * @constructor
 * @param {Map} map The map to manage.
 * @param {Object} opt_opts A container for optional arguments:
 *   {Number} maxZoom The maximum zoom level for which to create tiles.
 *   {Number} borderPadding The width in pixels beyond the map border,
 *                   where markers should be display.
 *   {Boolean} trackMarkers Whether or not this manager should track marker
 *                   movements.
 */
function MarkerManager(map, opt_opts) {
  var me = this;
  me.map_ = map;
  me.mapZoom_ = map.getZoom();
  me.projection_ = map.getCurrentMapType().getProjection();

  opt_opts = opt_opts || {};
  me.tileSize_ = MarkerManager.DEFAULT_TILE_SIZE_;
  
  var maxZoom = MarkerManager.DEFAULT_MAX_ZOOM_;
  if(opt_opts.maxZoom != undefined) {
    maxZoom = opt_opts.maxZoom;
  }
  me.maxZoom_ = maxZoom;

  me.trackMarkers_ = opt_opts.trackMarkers;

  var padding;
  if (typeof opt_opts.borderPadding == "number") {
    padding = opt_opts.borderPadding;
  } else {
    padding = MarkerManager.DEFAULT_BORDER_PADDING_;
  }
  // The padding in pixels beyond the viewport, where we will pre-load markers.
  me.swPadding_ = new GSize(-padding, padding);
  me.nePadding_ = new GSize(padding, -padding);
  me.borderPadding_ = padding;

  me.gridWidth_ = [];

  me.grid_ = [];
  me.grid_[maxZoom] = [];
  me.numMarkers_ = [];
  me.numMarkers_[maxZoom] = 0;

  GEvent.bind(map, "moveend", me, me.onMapMoveEnd_);

  // NOTE: These two closures provide easy access to the map.
  // They are used as callbacks, not as methods.
  me.removeOverlay_ = function(marker) {
    map.removeOverlay(marker);
    me.shownMarkers_--;
  };
  me.addOverlay_ = function(marker) {
    map.addOverlay(marker);
    me.shownMarkers_++;
  };

  me.resetManager_();
  me.shownMarkers_ = 0;

  me.shownBounds_ = me.getMapGridBounds_();
};

// Static constants:
MarkerManager.DEFAULT_TILE_SIZE_ = 1024;
MarkerManager.DEFAULT_MAX_ZOOM_ = 17;
MarkerManager.DEFAULT_BORDER_PADDING_ = 100;
MarkerManager.MERCATOR_ZOOM_LEVEL_ZERO_RANGE = 256;


/**
 * Initializes MarkerManager arrays for all zoom levels
 * Called by constructor and by clearAllMarkers
 */ 
MarkerManager.prototype.resetManager_ = function() {
  var me = this;
  var mapWidth = MarkerManager.MERCATOR_ZOOM_LEVEL_ZERO_RANGE;
  for (var zoom = 0; zoom <= me.maxZoom_; ++zoom) {
    me.grid_[zoom] = [];
    me.numMarkers_[zoom] = 0;
    me.gridWidth_[zoom] = Math.ceil(mapWidth/me.tileSize_);
    mapWidth <<= 1;
  }
};

/**
 * Removes all currently displayed markers
 * and calls resetManager to clear arrays
 */
MarkerManager.prototype.clearMarkers = function() {
  var me = this;
  me.processAll_(me.shownBounds_, me.removeOverlay_);
  me.resetManager_();
};


/**
 * Gets the tile coordinate for a given latlng point.
 *
 * @param {LatLng} latlng The geographical point.
 * @param {Number} zoom The zoom level.
 * @param {GSize} padding The padding used to shift the pixel coordinate.
 *               Used for expanding a bounds to include an extra padding
 *               of pixels surrounding the bounds.
 * @return {GPoint} The point in tile coordinates.
 *
 */
MarkerManager.prototype.getTilePoint_ = function(latlng, zoom, padding) {
  var pixelPoint = this.projection_.fromLatLngToPixel(latlng, zoom);
  return new GPoint(
      Math.floor((pixelPoint.x + padding.width) / this.tileSize_),
      Math.floor((pixelPoint.y + padding.height) / this.tileSize_));
};


/**
 * Finds the appropriate place to add the marker to the grid.
 * Optimized for speed; does not actually add the marker to the map.
 * Designed for batch-processing thousands of markers.
 *
 * @param {Marker} marker The marker to add.
 * @param {Number} minZoom The minimum zoom for displaying the marker.
 * @param {Number} maxZoom The maximum zoom for displaying the marker.
 */
MarkerManager.prototype.addMarkerBatch_ = function(marker, minZoom, maxZoom) {
  var mPoint = marker.getPoint();
  // Tracking markers is expensive, so we do this only if the
  // user explicitly requested it when creating marker manager.
  if (this.trackMarkers_) {
    GEvent.bind(marker, "changed", this, this.onMarkerMoved_);
  }

  var gridPoint = this.getTilePoint_(mPoint, maxZoom, GSize.ZERO);

  for (var zoom = maxZoom; zoom >= minZoom; zoom--) {
    var cell = this.getGridCellCreate_(gridPoint.x, gridPoint.y, zoom);
    cell.push(marker);

    gridPoint.x = gridPoint.x >> 1;
    gridPoint.y = gridPoint.y >> 1;
  }
};


/**
 * Returns whether or not the given point is visible in the shown bounds. This
 * is a helper method that takes care of the corner case, when shownBounds have
 * negative minX value.
 *
 * @param {Point} point a point on a grid.
 * @return {Boolean} Whether or not the given point is visible in the currently
 * shown bounds.
 */
MarkerManager.prototype.isGridPointVisible_ = function(point) {
  var me = this;
  var vertical = me.shownBounds_.minY <= point.y &&
      point.y <= me.shownBounds_.maxY;
  var minX = me.shownBounds_.minX;
  var horizontal = minX <= point.x && point.x <= me.shownBounds_.maxX;
  if (!horizontal && minX < 0) {
    // Shifts the negative part of the rectangle. As point.x is always less
    // than grid width, only test shifted minX .. 0 part of the shown bounds.
    var width = me.gridWidth_[me.shownBounds_.z];
    horizontal = minX + width <= point.x && point.x <= width - 1;
  }
  return vertical && horizontal;
}


/**
 * Reacts to a notification from a marker that it has moved to a new location.
 * It scans the grid all all zoom levels and moves the marker from the old grid
 * location to a new grid location.
 *
 * @param {Marker} marker The marker that moved.
 * @param {LatLng} oldPoint The old position of the marker.
 * @param {LatLng} newPoint The new position of the marker.
 */
MarkerManager.prototype.onMarkerMoved_ = function(marker, oldPoint, newPoint) {
  // NOTE: We do not know the minimum or maximum zoom the marker was
  // added at, so we start at the absolute maximum. Whenever we successfully
  // remove a marker at a given zoom, we add it at the new grid coordinates.
  var me = this;
  var zoom = me.maxZoom_;
  var changed = false;
  var oldGrid = me.getTilePoint_(oldPoint, zoom, GSize.ZERO);
  var newGrid = me.getTilePoint_(newPoint, zoom, GSize.ZERO);
  while (zoom >= 0 && (oldGrid.x != newGrid.x || oldGrid.y != newGrid.y)) {
    var cell = me.getGridCellNoCreate_(oldGrid.x, oldGrid.y, zoom);
    if (cell) {
      if (me.removeFromArray(cell, marker)) {
        me.getGridCellCreate_(newGrid.x, newGrid.y, zoom).push(marker);
      }
    }
    // For the current zoom we also need to update the map. Markers that no
    // longer are visible are removed from the map. Markers that moved into
    // the shown bounds are added to the map. This also lets us keep the count
    // of visible markers up to date.
    if (zoom == me.mapZoom_) {
      if (me.isGridPointVisible_(oldGrid)) {
        if (!me.isGridPointVisible_(newGrid)) {
          me.removeOverlay_(marker);
          changed = true;
        }
      } else {
        if (me.isGridPointVisible_(newGrid)) {
          me.addOverlay_(marker);
          changed = true;
        }
      }
    }
    oldGrid.x = oldGrid.x >> 1;
    oldGrid.y = oldGrid.y >> 1;
    newGrid.x = newGrid.x >> 1;
    newGrid.y = newGrid.y >> 1;
    --zoom;
  }
  if (changed) {
    me.notifyListeners_();
  }
};


/**
 * Searches at every zoom level to find grid cell
 * that marker would be in, removes from that array if found.
 * Also removes marker with removeOverlay if visible.
 * @param {GMarker} marker The marker to delete.
 */
MarkerManager.prototype.removeMarker = function(marker) {
  var me = this;
  var zoom = me.maxZoom_;
  var changed = false;
  var point = marker.getPoint();
  var grid = me.getTilePoint_(point, zoom, GSize.ZERO);
  while (zoom >= 0) {
    var cell = me.getGridCellNoCreate_(grid.x, grid.y, zoom);

    if (cell) {
      me.removeFromArray(cell, marker);
    }
    // For the current zoom we also need to update the map. Markers that no
    // longer are visible are removed from the map. This also lets us keep the count
    // of visible markers up to date.
    if (zoom == me.mapZoom_) {
      if (me.isGridPointVisible_(grid)) {
          me.removeOverlay_(marker);
          changed = true;
      } 
    }
    grid.x = grid.x >> 1;
    grid.y = grid.y >> 1;
    --zoom;
  }
  if (changed) {
    me.notifyListeners_();
  }
};


/**
 * Add many markers at once.
 * Does not actually update the map, just the internal grid.
 *
 * @param {Array of Marker} markers The markers to add.
 * @param {Number} minZoom The minimum zoom level to display the markers.
 * @param {Number} opt_maxZoom The maximum zoom level to display the markers.
 */
MarkerManager.prototype.addMarkers = function(markers, minZoom, opt_maxZoom) {
  var maxZoom = this.getOptMaxZoom_(opt_maxZoom);
  for (var i = markers.length - 1; i >= 0; i--) {
    this.addMarkerBatch_(markers[i], minZoom, maxZoom);
  }

  this.numMarkers_[minZoom] += markers.length;
};


/**
 * Returns the value of the optional maximum zoom. This method is defined so
 * that we have just one place where optional maximum zoom is calculated.
 *
 * @param {Number} opt_maxZoom The optinal maximum zoom.
 * @return The maximum zoom.
 */
MarkerManager.prototype.getOptMaxZoom_ = function(opt_maxZoom) {
  return opt_maxZoom != undefined ? opt_maxZoom : this.maxZoom_;
}


/**
 * Calculates the total number of markers potentially visible at a given
 * zoom level.
 *
 * @param {Number} zoom The zoom level to check.
 */
MarkerManager.prototype.getMarkerCount = function(zoom) {
  var total = 0;
  for (var z = 0; z <= zoom; z++) {
    total += this.numMarkers_[z];
  }
  return total;
};


/**
 * Add a single marker to the map.
 *
 * @param {Marker} marker The marker to add.
 * @param {Number} minZoom The minimum zoom level to display the marker.
 * @param {Number} opt_maxZoom The maximum zoom level to display the marker.
 */
MarkerManager.prototype.addMarker = function(marker, minZoom, opt_maxZoom) {
  var me = this;
  var maxZoom = this.getOptMaxZoom_(opt_maxZoom);
  me.addMarkerBatch_(marker, minZoom, maxZoom);
  var gridPoint = me.getTilePoint_(marker.getPoint(), me.mapZoom_, GSize.ZERO);
  if(me.isGridPointVisible_(gridPoint) && 
     minZoom <= me.shownBounds_.z &&
     me.shownBounds_.z <= maxZoom ) {
    me.addOverlay_(marker);
    me.notifyListeners_();
  }
  this.numMarkers_[minZoom]++;
};

/**
 * Returns true if this bounds (inclusively) contains the given point.
 * @param {Point} point  The point to test.
 * @return {Boolean} This Bounds contains the given Point.
 */
GBounds.prototype.containsPoint = function(point) {
  var outer = this;
  return (outer.minX <= point.x &&
          outer.maxX >= point.x &&
          outer.minY <= point.y &&
          outer.maxY >= point.y);
}

/**
 * Get a cell in the grid, creating it first if necessary.
 *
 * Optimization candidate
 *
 * @param {Number} x The x coordinate of the cell.
 * @param {Number} y The y coordinate of the cell.
 * @param {Number} z The z coordinate of the cell.
 * @return {Array} The cell in the array.
 */
MarkerManager.prototype.getGridCellCreate_ = function(x, y, z) {
  var grid = this.grid_[z];
  if (x < 0) {
    x += this.gridWidth_[z];
  }
  var gridCol = grid[x];
  if (!gridCol) {
    gridCol = grid[x] = [];
    return gridCol[y] = [];
  }
  var gridCell = gridCol[y];
  if (!gridCell) {
    return gridCol[y] = [];
  }
  return gridCell;
};


/**
 * Get a cell in the grid, returning undefined if it does not exist.
 *
 * NOTE: Optimized for speed -- otherwise could combine with getGridCellCreate_.
 *
 * @param {Number} x The x coordinate of the cell.
 * @param {Number} y The y coordinate of the cell.
 * @param {Number} z The z coordinate of the cell.
 * @return {Array} The cell in the array.
 */
MarkerManager.prototype.getGridCellNoCreate_ = function(x, y, z) {
  var grid = this.grid_[z];
  if (x < 0) {
    x += this.gridWidth_[z];
  }
  var gridCol = grid[x];
  return gridCol ? gridCol[y] : undefined;
};


/**
 * Turns at geographical bounds into a grid-space bounds.
 *
 * @param {LatLngBounds} bounds The geographical bounds.
 * @param {Number} zoom The zoom level of the bounds.
 * @param {GSize} swPadding The padding in pixels to extend beyond the
 * given bounds.
 * @param {GSize} nePadding The padding in pixels to extend beyond the
 * given bounds.
 * @return {GBounds} The bounds in grid space.
 */
MarkerManager.prototype.getGridBounds_ = function(bounds, zoom, swPadding,
                                                  nePadding) {
  zoom = Math.min(zoom, this.maxZoom_);
  
  var bl = bounds.getSouthWest();
  var tr = bounds.getNorthEast();
  var sw = this.getTilePoint_(bl, zoom, swPadding);
  var ne = this.getTilePoint_(tr, zoom, nePadding);
  var gw = this.gridWidth_[zoom];
  
  // Crossing the prime meridian requires correction of bounds.
  if (tr.lng() < bl.lng() || ne.x < sw.x) {
    sw.x -= gw;
  }
  if (ne.x - sw.x  + 1 >= gw) {
    // Computed grid bounds are larger than the world; truncate.
    sw.x = 0;
    ne.x = gw - 1;
  }
  var gridBounds = new GBounds([sw, ne]);
  gridBounds.z = zoom;
  return gridBounds;
};


/**
 * Gets the grid-space bounds for the current map viewport.
 *
 * @return {Bounds} The bounds in grid space.
 */
MarkerManager.prototype.getMapGridBounds_ = function() {
  var me = this;
  return me.getGridBounds_(me.map_.getBounds(), me.mapZoom_,
                           me.swPadding_, me.nePadding_);
};


/**
 * Event listener for map:movend.
 * NOTE: Use a timeout so that the user is not blocked
 * from moving the map.
 *
 */
MarkerManager.prototype.onMapMoveEnd_ = function() {
  var me = this;
  me.objectSetTimeout_(this, this.updateMarkers_, 0);
};


/**
 * Call a function or evaluate an expression after a specified number of
 * milliseconds.
 *
 * Equivalent to the standard window.setTimeout function, but the given
 * function executes as a method of this instance. So the function passed to
 * objectSetTimeout can contain references to this.
 *    objectSetTimeout(this, function() { alert(this.x) }, 1000);
 *
 * @param {Object} object  The target object.
 * @param {Function} command  The command to run.
 * @param {Number} milliseconds  The delay.
 * @return {Boolean}  Success.
 */
MarkerManager.prototype.objectSetTimeout_ = function(object, command, milliseconds) {
  return window.setTimeout(function() {
    command.call(object);
  }, milliseconds);
};


/**
 * Refresh forces the marker-manager into a good state.
 * <ol>
 *   <li>If never before initialized, shows all the markers.</li>
 *   <li>If previously initialized, removes and re-adds all markers.</li>
 * </ol>
 */
MarkerManager.prototype.refresh = function() {
  var me = this;
  if (me.shownMarkers_ > 0) {
    me.processAll_(me.shownBounds_, me.removeOverlay_);
  }
  me.processAll_(me.shownBounds_, me.addOverlay_);
  me.notifyListeners_();
};


/**
 * After the viewport may have changed, add or remove markers as needed.
 */
MarkerManager.prototype.updateMarkers_ = function() {
  var me = this;
  me.mapZoom_ = this.map_.getZoom();
  var newBounds = me.getMapGridBounds_();
  
  // If the move does not include new grid sections,
  // we have no work to do:
  if (newBounds.equals(me.shownBounds_) && newBounds.z == me.shownBounds_.z) {
    return;
  }

  if (newBounds.z != me.shownBounds_.z) {
    me.processAll_(me.shownBounds_, me.removeOverlay_);
    me.processAll_(newBounds, me.addOverlay_);
  } else {
    // Remove markers:
    me.rectangleDiff_(me.shownBounds_, newBounds, me.removeCellMarkers_);

    // Add markers:
    me.rectangleDiff_(newBounds, me.shownBounds_, me.addCellMarkers_);
  }
  me.shownBounds_ = newBounds;

  me.notifyListeners_();
};


/**
 * Notify listeners when the state of what is displayed changes.
 */
MarkerManager.prototype.notifyListeners_ = function() {
  GEvent.trigger(this, "changed", this.shownBounds_, this.shownMarkers_);
};


/**
 * Process all markers in the bounds provided, using a callback.
 *
 * @param {Bounds} bounds The bounds in grid space.
 * @param {Function} callback The function to call for each marker.
 */
MarkerManager.prototype.processAll_ = function(bounds, callback) {
  for (var x = bounds.minX; x <= bounds.maxX; x++) {
    for (var y = bounds.minY; y <= bounds.maxY; y++) {
      this.processCellMarkers_(x, y,  bounds.z, callback);
    }
  }
};


/**
 * Process all markers in the grid cell, using a callback.
 *
 * @param {Number} x The x coordinate of the cell.
 * @param {Number} y The y coordinate of the cell.
 * @param {Number} z The z coordinate of the cell.
 * @param {Function} callback The function to call for each marker.
 */
MarkerManager.prototype.processCellMarkers_ = function(x, y, z, callback) {
  var cell = this.getGridCellNoCreate_(x, y, z);
  if (cell) {
    for (var i = cell.length - 1; i >= 0; i--) {
      callback(cell[i]);
    }
  }
};


/**
 * Remove all markers in a grid cell.
 *
 * @param {Number} x The x coordinate of the cell.
 * @param {Number} y The y coordinate of the cell.
 * @param {Number} z The z coordinate of the cell.
 */
MarkerManager.prototype.removeCellMarkers_ = function(x, y, z) {
  this.processCellMarkers_(x, y, z, this.removeOverlay_);
};


/**
 * Add all markers in a grid cell.
 *
 * @param {Number} x The x coordinate of the cell.
 * @param {Number} y The y coordinate of the cell.
 * @param {Number} z The z coordinate of the cell.
 */
MarkerManager.prototype.addCellMarkers_ = function(x, y, z) {
  this.processCellMarkers_(x, y, z, this.addOverlay_);
};


/**
 * Use the rectangleDiffCoords function to process all grid cells
 * that are in bounds1 but not bounds2, using a callback, and using
 * the current MarkerManager object as the instance.
 *
 * Pass the z parameter to the callback in addition to x and y.
 *
 * @param {Bounds} bounds1 The bounds of all points we may process.
 * @param {Bounds} bounds2 The bounds of points to exclude.
 * @param {Function} callback The callback function to call
 *                   for each grid coordinate (x, y, z).
 */
MarkerManager.prototype.rectangleDiff_ = function(bounds1, bounds2, callback) {
  var me = this;
  me.rectangleDiffCoords(bounds1, bounds2, function(x, y) {
    callback.apply(me, [x, y, bounds1.z]);
  });
};


/**
 * Calls the function for all points in bounds1, not in bounds2
 *
 * @param {Bounds} bounds1 The bounds of all points we may process.
 * @param {Bounds} bounds2 The bounds of points to exclude.
 * @param {Function} callback The callback function to call
 *                   for each grid coordinate.
 */
MarkerManager.prototype.rectangleDiffCoords = function(bounds1, bounds2, callback) {
  var minX1 = bounds1.minX;
  var minY1 = bounds1.minY;
  var maxX1 = bounds1.maxX;
  var maxY1 = bounds1.maxY;
  var minX2 = bounds2.minX;
  var minY2 = bounds2.minY;
  var maxX2 = bounds2.maxX;
  var maxY2 = bounds2.maxY;

  for (var x = minX1; x <= maxX1; x++) {  // All x in R1
    // All above:
    for (var y = minY1; y <= maxY1 && y < minY2; y++) {  // y in R1 above R2
      callback(x, y);
    }
    // All below:
    for (var y = Math.max(maxY2 + 1, minY1);  // y in R1 below R2
         y <= maxY1; y++) {
      callback(x, y);
    }
  }

  for (var y = Math.max(minY1, minY2);
       y <= Math.min(maxY1, maxY2); y++) {  // All y in R2 and in R1
    // Strictly left:
    for (var x = Math.min(maxX1 + 1, minX2) - 1;
         x >= minX1; x--) {  // x in R1 left of R2
      callback(x, y);
    }
    // Strictly right:
    for (var x = Math.max(minX1, maxX2 + 1);  // x in R1 right of R2
         x <= maxX1; x++) {
      callback(x, y);
    }
  }
};


/**
 * Removes value from array. O(N).
 *
 * @param {Array} array  The array to modify.
 * @param {any} value  The value to remove.
 * @param {Boolean} opt_notype  Flag to disable type checking in equality.
 * @return {Number}  The number of instances of value that were removed.
 */
MarkerManager.prototype.removeFromArray = function(array, value, opt_notype) {
  var shift = 0;
  for (var i = 0; i < array.length; ++i) {
    if (array[i] === value || (opt_notype && array[i] == value)) {
      array.splice(i--, 1);
      shift++;
    }
  }
  return shift;
};
/*
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
/**
 * @name Tabbed Max Content
 * @version 1.0
 * @author: Nianwei Liu [nianwei at gmail dot com]
 * @fileoverview This library provides a max info window UI that's similar
 *  to the info window UI for local business results on Google Maps. It lets a
 *  developer pass in an array of content that will be rendered in tabs in the
 *  maximized state of an info window.
 */
(function () {
  /*jslint browser:true */
  /*global GMap2,GMarker,GEvent */
  var defaultStyle = {
    tabBar: {
      background: '#F4F4F4 none repeat scroll 0 0',
      borderBottom: '1px solid #B0B0B0',
      padding: '6px 8px 4px',
      marginRight: '13px',
      whiteSpace: 'nowrap',
      verticalAlign: 'bottom'
    },
    tabLeft: {},
    tabRight: {},
    tabOn: {
      background: '#FFFFFF none repeat scroll 0 0',
      padding: '6px 8px 4px',
      borderTop: '1px solid #B0B0B0',
      borderLeft:  '1px solid #B0B0B0',
      borderRight:  '1px solid #B0B0B0',
      borderBottom: '2px solid #FFFFFF',
      color: '#000000',
      textDecoration: 'none',
      fontWeight: 'bold'
    },
    tabOff: {
      background: '#F4F4F4 none repeat scroll 0 0',
      padding: '6px 8px 4px',
      color: '#0000FF',
      border: 'none',
      textDecoration: 'underline',
      fontWeight: 'normal'
    },
    content: {
      borderStyle: 'none solid solid solid',
      borderWidth: '1px',
      borderColor: '#B0B0B0',
      borderTop: 'none',
      overflow: 'auto'
    },
    summary: {
      overflow: 'auto',
      marginBottom: '5px'
    }
  };
  /**
   * set the property of object from another object
   * @param {Object} obj target object
   * @param {Object} vals source object
   */
  var setVals = function (obj, vals) {
    if (obj && vals) {
      for (var x in vals) {
        if (vals.hasOwnProperty(x)) {
          if (obj[x] && typeof vals[x] === 'object') {
            obj[x] = setVals(obj[x], vals[x]);
          } else {
            obj[x] = vals[x];
          }
        }
      }
    }
    return obj;
  };
  /**
   * Create an element
   * @param {String} tag of element
   * @param {Object} attrs name-value of attributes as json
   * @param {String|Node} content DOM node or HTML
   * @param {Object} style css object to set to the element
   * @param {Node} parent if supplied, the node will be appended to the parent
   * @return {Node} the new or modified node
   */
  var createEl = function (tag, attrs, content, style, parent) {
    var node = content;
    if (!content || (content && typeof content === 'string')) {
      node = document.createElement(tag);
      node.innerHTML = content || '';
    }
    if (style) {
      setVals(node.style, style);
    }
    if (attrs) {
      setVals(node, attrs);
    }
    if (parent) {
      parent.appendChild(node);
    }
    return node;
  };

  /**
   * Get the offset position up to given parent
   * @param {Node} el
   * @param {Node} parent if null will get the DOM root.
   */
  var getPosition = function (el, parent) {
    var leftPos = 0;
    var topPos = 0;
    var par = el;
    while (par && par !== parent) {
      leftPos += par.offsetLeft;
      topPos += par.offsetTop;
      par = par.offsetParent;
    }
    return {
      left: leftPos,
      top: topPos
    };
  };

  /**
   * Creates a content tab data structure that can be passed in the <code>tabs</code> argument
   * in the <code>openMaxContentTabs*()</code> methods.
   * @name MaxContentTab
   * @class This class represents a tab in the maximized info window. An array of
   *  instances of this class can be passed in as the {@link tabs} argument to
   *  the methods <code>openMaxContentTabs*()</code> etc.
   * This class is similar to the
   * <a target=_blank href=http://code.google.com/apis/maps/documentation/reference.html#GInfoWindowTab>GInfoWindowTab</a>
   * class in the core API.
   * @param {String} label
   * @param {Node|String} content
   */
  function MaxContentTab(label, content) {
    this.label_ = label;
    this.contentNode_ = createEl('div', null, content, null, null);
    this.navNode_ = null;
  }

   /**
   * Returns the label of the tab.
   * @return {String} label
   */
  MaxContentTab.prototype.getLabel = function () {
    return this.label_;
  };

  /**
   * Returns the content of the tab.
   * @return {Node} conent
   */
  MaxContentTab.prototype.getContentNode = function () {
    return this.contentNode_;
  };

 /**
 * @name TabbedMaxContent
 * @class This class represent the max content in the info window.
 * There is no public constructor for this class. If needed, it can be accessed
 * via  <code>GMap2.getTabbedMaxContent()</code>.
 * @param {GInfoWindow} iw
 */
  function TabbedMaxContent(iw) {
    this.infoWindow_ = iw;
    GEvent.bind(iw, 'maximizeclick', this, this.onMaximizeClick_);
    GEvent.bind(iw, 'restoreclick', this, this.onRestoreClick_);
    GEvent.bind(iw, 'maximizeend', this, this.onMaximizeEnd_);
    this.style_ = {};
    this.maxNode_ = null;
    this.summaryNode_ = null;
    this.navsNode_ = null;
    this.contentsNode_ = null;
    this.tabs_ = [];
  }

  /**
   * Before open infowindow, setup contents
   * @param {Node} sumNode summary node
   * @param {GInfoWindowTabs[]} tabs
   * @param {MaxInfoWindowOptions} opt_maxOptions
   * @private
   */
  TabbedMaxContent.prototype.initialize_ = function (sumNode, tabs, opt_maxOptions) {
    this.tabs_ = tabs;
    this.selectedTab_ = -1;
    if (this.maxNode_) {
      GEvent.clearNode(this.maxNode_);
      this.maxNode_.innerHTML = '';
    } else {
      this.maxNode_ = createEl('div', {
        id: 'maxcontent'
      });
    }
    opt_maxOptions = opt_maxOptions || {};
    var selectedTab = opt_maxOptions.selectedTab || 0;
    this.style_ = setVals({}, defaultStyle);
    this.style_ = setVals(this.style_, opt_maxOptions.style);
    this.summaryNode_ = createEl('div', null, sumNode, this.style_.summary, this.maxNode_);
    this.navsNode_ = createEl('div', null, null, this.style_.tabBar, this.maxNode_);
    this.contentsNode_ = createEl('div', null, null, null, this.maxNode_);
    if (tabs && tabs.length) {
      // left
      createEl('span', null, null, this.style_.tabLeft, this.navsNode_);
      for (var i = 0, ct = tabs.length; i < ct; i++) {
        if (i === selectedTab || tabs[i].getLabel() === selectedTab) {
          this.selectedTab_ = i;
        }
        tabs[i].navNode_ = createEl('span', null, tabs[i].getLabel(), this.style_.tabOff, this.navsNode_);//);
        var node = createEl('div', null, tabs[i].getContentNode(), this.style_.content, this.contentsNode_);
        node.style.display = 'none';
      }
      // right
      createEl('span', null, null, this.style_.tabRight, this.navsNode_);
    }
  };
  /**
   * Setup event listeners. The core API seems removed all liteners when restored to normal size
   * @private
   */
  TabbedMaxContent.prototype.onMaximizeClick_ = function () {
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      GEvent.addDomListener(this.tabs_[i].navNode_, 'click', GEvent.callback(this, this.selectTab, i));
    }
  };
  /**
   * Clean up listeners on tabs.
   * @private
   */
  TabbedMaxContent.prototype.onRestoreClick_ = function () {
    if (this.maxNode_) {
      GEvent.clearNode(this.maxNode_);
    }
  };
  /**
   * Clean up listeners on tabs.
   * @private
   */
  TabbedMaxContent.prototype.onMaximizeEnd_ = function () {
    this.checkResize();
    this.selectTab(this.selectedTab_);
  };
  /**
   * Select a tab using the given index or label.
   * @param {Number|String} identifier
   */
  TabbedMaxContent.prototype.selectTab = function (identifier) {
    var trigger = false;
    var hasVisibleTab = false;
    var tab;
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      tab = this.tabs_[i];
      if (i === identifier || tab.getLabel() === identifier) {
        if (tab.getContentNode().style.display === 'none') {
          setVals(tab.navNode_.style, this.style_.tabOn);
          tab.getContentNode().style.display = 'block';
          this.selectedTab_ = i;
          trigger = true;
        }
        hasVisibleTab = true;
      } else {
        setVals(tab.navNode_.style, this.style_.tabOff);
        tab.getContentNode().style.display = 'none';
      }
    }
    // avoid excessive event if clicked on a selected tab.
    if (trigger) {
      /**
       * This event is fired after a tab is selected,
       * passing the selected {@link MaxContentTab} into the callback.
       * @name TabbedMaxContent#selecttab
       * @param {MaxContentTab} selected tab
       * @event
       */
      GEvent.trigger(this, 'selecttab', this.tabs_[this.selectedTab_]);
    }
    if (!hasVisibleTab) {
      this.selectTab(0);
    }
  };
  /**
   * Return the {@link MaxContentTab} at the given index or label.
   * @param {Number|String} identifier
   * @return {MaxContentTab}
   */
  TabbedMaxContent.prototype.getTab = function (identifier) {
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      if (i === identifier || this.tabs_[i].getLabel() === identifier) {
        return this.tabs_[i];
      }
    }
  };

  /**
   * Adjust sizes of tabs to fit inside the maximized info window.
   * This method is automatically called on <code>
   * GInfoWindow</code>'s <code>'maximizeend'</code> event. However, there may
   * be cases where additional content is loaded in after that event,
   * and an additional resize is needed.
   */
  TabbedMaxContent.prototype.checkResize = function () {
    var container = this.infoWindow_.getContentContainers()[0];
    var contents = this.contentsNode_;
    var pos = getPosition(contents, container);
    for (var i = 0, ct = this.tabs_.length; i < ct; i++) {
      var t = this.tabs_[i].getContentNode();
      t.style.width = container.style.width;
      t.style.height = (parseInt(container.style.height, 10) - pos.top) + 'px';
    }
  };


  /**
   * @name MaxContentOptions
   * @class
   * This class extends <a href='http://code.google.com/apis/maps/documentation/reference.ht    ml#GInfoWindowOptions'><code>GInfoWindowOptions</code></a>.
   * Instances of this class are used in the <code>opts_maxOption</code>
   * argument to methods openMaxContentTabs(), openMaxContentTabsHtml().
   * Note, <code>GInfoWindowOptions.maxContent</code> can not be specified.
   * @property {Object} [style] The object that holds a set of css styles
   * for the maximized content. It has the following properties:
   *     <code> tabOn, tabOff, tabBar, tabLeft, tabRight, content </code>.
   *  Each property is a css object such as
   *     <code> {backgroundColor: 'gray', opacity: 0.2}</code>.
   * @property {Number|String} [selectedTab = 0] Selects the tab with the given
   * index or name by default when the info window is first maximized.
   * @property {String|Node} [maxTitle = ""] Specifies the title to be shown when
   * the infowindow is maximized.
   * @property {Boolean} [maximized = false] Specifies if the window should be
   * opened in the maximized state by default.
   */

  /**
   * @name GMap2
   * @class These are new methods added to the Google Maps API's
   * <a href  = 'http://code.google.com/apis/maps/documentation/reference.html#GMap2'>GMap2</a>
   * class.
   */
  /**
   * Opens an info window with maximizable content at the given {@link latlng}.
   * The infowindow displays the content in the {@link minNode} in the
   * minimized state, and then displays the content in the {@link summaryNode}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GLatLng} latlng
   * @param {Node} minNode
   * @param {Node} summaryNode
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMap2.prototype.openMaxContentTabs = function (latlng, minNode, sumNode, tabs, opt_maxOptions) {
    var max = this.getTabbedMaxContent();
    var opts = opt_maxOptions || {};
    max.initialize_(sumNode, tabs, opts);
    opts.maxContent = max.maxNode_;
    if (opts.style) {
      delete opts.style;
    }
    if (opts.selectedTab) {
      delete opts.selectedTab;
    }
    if (minNode.style) {
      minNode.style.marginTop = '6px';
    }
    this.openInfoWindow(latlng, minNode, opts);
    if (opts.maximized) {
      var iw = this.getInfoWindow();
      var m = GEvent.addListener(this, 'infowindowopen', function () {
        GEvent.removeListener(m);
        iw.maximize();
      });
    }
  };

  /**
   * Opens an info window with maximizable content at the given {@link latlng}.
   * The infowindow displays the content in the {@link minHtml} in the
   * minimized state, and then displays the content in the {@link summaryHtml}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GLatLng} latlng
   * @param {String} minHtml
   * @param {String} summaryHtml
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMap2.prototype.openMaxContentTabsHtml = function (latlng, html, summary, tabs, opt_maxOptions) {
    this.openMaxContentTabs(latlng, createEl('div', null, html), createEl('div', null, summary), tabs, opt_maxOptions);
  };

  /**
   * Returns the {@link TabbedMaxContent} for currently opened info window.
   * @return {TabbedMaxContent}
   */
  GMap2.prototype.getTabbedMaxContent = function () {
    this.maxContent_  = this.maxContent_ || new TabbedMaxContent(this.getInfoWindow());
    return this.maxContent_;
  };

  /**
   * @name GMarker
   * @class These are new methods added to Google Maps API's
   * <a href  = 'http://code.google.com/apis/maps/documentation/reference.html#GMarker'>GMarker</a>
   * class.
   */

  /**
   * Opens an info window with maximizable content above the marker.
   * The infowindow displays the content in the {@link minHtml} in the
   * minimized state, and then displays the content in the {@link summaryHtml}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GMap2} map
   * @param {String} minHtml
   * @param {String} summaryHtml
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMarker.prototype.openMaxContentTabsHtml = function (map, minHtml, summaryHtml, tabs, opt_maxOptions) {
    map.openMaxContentTabsHtml(this.getLatLng(), minHtml, summaryHtml, tabs, opt_maxOptions);
  };

  /**
   * Opens an info window with maximizable content above the marker.
   * The infowindow displays the content in the {@link minNode} in the
   * minimized state, and then displays the content in the {@link summaryNode}
   * along with the array of {@link tabs} in the maximized state.
   * Additional options can be sent in {@link opt_maxOptions}.
   * @param {GMap2} map
   * @param {Node} minNode
   * @param {Node} summaryNode
   * @param {MaxContentTab[]} tabs
   * @param {MaxContentOptions} opt_maxOptions
   */
  GMarker.prototype.openMaxContentTabs = function (map, minNode, summaryNode, tabs, opt_maxOptions) {
    map.openMaxContentTabs(this.getLatLng(), minNode, summaryNode, tabs, opt_maxOptions);
  };

  window.MaxContentTab = MaxContentTab;
})();
GMap2.prototype.openInfoWindowTabsMaxTabs = function(latlng, tabs, maxTabs, opts)
{
    var tabbedMaxContent = this.getTabbedMaxContent();
    opts = opts || {};
    tabbedMaxContent.initialize_("", maxTabs, opts);
    opts.maxContent = tabbedMaxContent.maxNode_;
    this.openInfoWindowTabs(latlng, tabs, opts);
};

function getMapCenter(map, point_data, initialZoom)
{
    var baseWidth = Math.abs(map.getBounds().getNorthEast().x) * 2;
    var baseHeight = Math.abs(map.getBounds().getNorthEast().y) * 2;

    var minLat = 99999999;
    var minLng = 99999999;
    var maxLat = -99999999;
    var maxLng = -99999999;

    var i;

    for(i = 0; i < point_data.length; i++)
    {
        var lat = point_data[i].lat;
        var lng = point_data[i].lng;

        if(lat < minLat) minLat = lat;
        if(lat > maxLat) maxLat = lat;
        if(lng < minLng) minLng = lng;
        if(lng > maxLng) maxLng = lng;
    }

    var wZoom;
    var w = Math.abs(maxLng - minLng);
    for(wZoom = initialZoom; wZoom >= 0; wZoom--)
    {
        if(baseWidth > w * 1.3)
        {
            break;
        }
        baseWidth *= 2;
    }

    var hZoom;
    var h = Math.abs(maxLat - minLat);
    for(hZoom = initialZoom; hZoom >= 0; hZoom--)
    {
        if(baseHeight > h * 1.3)
        {
            break;
        }
        baseHeight *= 2;
    }

    return {latlng: new GLatLng((minLat + maxLat) / 2, (minLng + maxLng) / 2),
            zoom: Math.min(wZoom, hZoom)};
}

function createTransportationMarker(transportation, latlng)
{
    var icon = new GIcon(G_DEFAULT_ICON, transportation.means ? "/media/images/transportation/" + transportation.means + ".png" : null);
    icon.shadow = "";
    icon.iconSize = new GSize(24, 24);
    return new GMarker(latlng, {icon: icon, hide: transportation.means == 0});
}

function initTripMap(point_data, bind_events)
{
    if (!GBrowserIsCompatible())
    {
        return;
    }

    var initialZoom = 9;

    transportation_markers = {}; // JS::global-var

    map = new GMap2(document.getElementById('map')); // JS::global-var
    map.addControl(new GLargeMapControl());
    map.setCenter(new GLatLng(0, 0), initialZoom);

    var mapCenter = getMapCenter(map, point_data, initialZoom);
    map.setCenter(mapCenter.latlng, mapCenter.zoom);

    function addListener(overlay, id, i)
    {
        GEvent.addListener(overlay, 'click',
            function(latlng) {
                var children = $(id).children().clone(true);
                if (children.length == 1)
                {
                    var child = $(children[0]);
                    map.openInfoWindow(latlng, child.find('.short-content')[0], {maxContent: child.find('.full-content')[0]});
                }
                else
                {
                    function tabname(i, j) { // give friendly name to tabs for Start/End
                        if (i == 0 && point_data[0].place_id == point_data[point_data.length - 1].place_id) {
                            if(j == 0)
                            {
                                return "Start";
                            }
                            else if (j == children.length - 1)
                            {
                                return "End";
                            }
                        }
                        return ordinal(j + 1);
                    }
                    var tabs = $.map(children, function(c, j) { return new GInfoWindowTab(tabname(i, j), $(c).find('.short-content')[0]); });
                    if($.grep(children, function(c) { return $(c).find('.full-content').length != 0; }).length == 0) // all the tabs only have short content
                    {
                        map.openInfoWindowTabs(latlng, tabs);
                    }
                    else
                    {
                        var maxTabs = $.map(children, function(c, j) { return new MaxContentTab(tabname(i, j), $(c).find('.full-content')[0]); });
                        map.openInfoWindowTabsMaxTabs(latlng, tabs, maxTabs);
                    }
                }
            });
    }

    var markers = [];
    for(var i = 0, addedOverlays = []; i < point_data.length; i++)
    {
        // draw segment
        if (i + 1 < point_data.length) { // there is no segment starting from the last point
            var p1 = point_data[i];
            var p2 = point_data[i + 1];
            var segment = [Math.min(p1.place_id, p2.place_id), Math.max(p1.place_id, p2.place_id)];
            var place_id_pair = segment[0] + "-" + segment[1];
            if($.inArray(place_id_pair, addedOverlays) == -1) {
                var line = new GPolyline([new GLatLng(p1.lat, p1.lng), new GLatLng(p2.lat, p2.lng)], "#ff0000", 3);
                if(bind_events)
                {
                    addListener(line, "#segment-data #place-pair-" + place_id_pair, i);
                    GEvent.addListener(line, 'mouseover', function() { document.body.style.cursor = 'hand'; });
                    GEvent.addListener(line, 'mouseout', function() { document.body.style.cursor = 'auto'; });
                }
                map.addOverlay(line);

                if (p1.transportation && p1.transportation.length != 0)
                {
                    var transportation = p1.transportation[0];
                    var marker = createTransportationMarker(transportation, new GLatLng((p1.lat + p2.lat) / 2, (p1.lng + p2.lng) / 2));
                    if(bind_events)
                    {
                        addListener(marker, "#segment-data #place-pair-" + place_id_pair, i);
                    }

                    markers.push(marker);
                    transportation_markers[transportation.annotation_id] = marker;
                }

                addedOverlays.push(place_id_pair);
            }
        }

        // draw point
        var p = point_data[i];
        if($.inArray(p.place_id, addedOverlays) == -1) {
            var icon = G_DEFAULT_ICON;
            if (!p.visited)
            {
                icon = new GIcon(G_DEFAULT_ICON, "/media/images/marker_grey.png");
            }
            if (i == 0 || i == point_data.length - 1)
            {
                icon = new GIcon(G_DEFAULT_ICON, "/media/images/marker_green.png");
            }
            var marker = new GMarker(new GLatLng(p.lat, p.lng), {title: p.name, icon: icon});
            if(bind_events)
            {
                addListener(marker, "#point-data #place-" + p.place_id, i);
            }
            markers.push(marker);
            addedOverlays.push(p.place_id);
        }
    }

    setTimeout(function() {
                   marker_manager = new MarkerManager(map); // JS::global-var
                   marker_manager.addMarkers(markers, 1);
                   marker_manager.refresh();
               }, 0);
}

function cleanupMap()
{
    GUnload();
}

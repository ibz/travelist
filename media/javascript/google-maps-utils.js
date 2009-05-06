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
        if(baseWidth > w * 1.1)
        {
            break;
        }
        baseWidth *= 2;
    }

    var hZoom;
    var h = Math.abs(maxLat - minLat);
    for(hZoom = initialZoom; hZoom >= 0; hZoom--)
    {
        if(baseHeight > h * 1.1)
        {
            break;
        }
        baseHeight *= 2;
    }

    return {latlng: new GLatLng((minLat + maxLat) / 2, (minLng + maxLng) / 2),
            zoom: Math.min(wZoom, hZoom)};
}

function initTripMap(id, point_data, bind_events)
{
    if (!GBrowserIsCompatible())
    {
        return;
    }

    var initialZoom = 16;

    var map = new GMap2(document.getElementById(id));
    map.addControl(new GLargeMapControl());
    map.setCenter(new GLatLng(0, 0), initialZoom);

    var mapCenter = getMapCenter(map, point_data, initialZoom);
    map.setCenter(mapCenter.latlng, mapCenter.zoom);

    function addListener(overlay, id) {
        GEvent.addListener(overlay, 'click',
            function(latlng) {
                var children = $(id).children().clone(true);
                if (children.length == 1) {
                    var child = $(children[0]);
                    map.openInfoWindow(latlng, child.find('.short-content')[0], {maxContent: child.find('.full-content')[0]});
                } else {
                    var tabname = function(i) { return i == 0 ? "Start" : i == children.length - 1 ? "End" : ordinal(i + 1); };
                    var tabs = $.map(children, function(c, i) { return new GInfoWindowTab(tabname(i), $(c).find('.short-content')[0]); });
                    if($.grep(children, function(c) { return $(c).find('.full-content').length != 0; }).length == 0) { // all the tabs only have short content
                        map.openInfoWindowTabs(latlng, tabs);
                    } else {
                        var maxTabs = $.map(children, function(c, i) { return new MaxContentTab(tabname(i), $(c).find('.full-content')[0]); });
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
            if($.inArray(segment, addedOverlays) == -1) {
                var line = new GPolyline([new GLatLng(p1.lat, p1.lng), new GLatLng(p2.lat, p2.lng)], "#ff0000", 3);
                if(bind_events) {
                    addListener(line, "#segment-data #place-pair-" + segment[0] + "-" + segment[1]);
                }
                map.addOverlay(line);
                addedOverlays.push(segment);
            }
        }

        // draw point
        var p = point_data[i];
        if($.inArray(p.place_id, addedOverlays) == -1) {
            var icon = G_DEFAULT_ICON;
            if (!p.visited) {
                icon = new GIcon(G_DEFAULT_ICON, "/media/images/marker_grey.png");
            }
            if (i == 0 || i == point_data.length - 1) {
                icon = new GIcon(G_DEFAULT_ICON, "/media/images/marker_green.png");
            }
            var marker = new GMarker(new GLatLng(p.lat, p.lng), {title: p.name, icon: icon});
            if(bind_events) {
                addListener(marker, "#point-data #place-" + p.place_id);
            }
            markers.push(marker);
            addedOverlays.push(p.place_id);
        }
    }

    setTimeout(function() {
                   var mgr = new MarkerManager(map);
                   mgr.addMarkers(markers, 1);
                   mgr.refresh();
               }, 0);
}

function cleanupMap()
{
    GUnload();
}

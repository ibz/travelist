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

function initUserMap(point_data)
{
    if (!GBrowserIsCompatible())
    {
        return;
    }

    var initialZoom = 9;

    var map = new GMap2(document.getElementById('map'));
    map.addControl(new GLargeMapControl());
    map.setCenter(new GLatLng(0, 0), initialZoom);

    var mapCenter = getMapCenter(map, point_data, initialZoom);
    map.setCenter(mapCenter.latlng, mapCenter.zoom);

    var markers = [];
    for(var i = 0; i < point_data.length; i++)
    {
        var p = point_data[i];
        var visit_count_text = "visited " + p.visit_count + " time" + (p.visit_count == 1 ? "" : "s");
        var marker = new GMarker(new GLatLng(p.lat, p.lng), {title: p.name + ", " + visit_count_text, icon: G_DEFAULT_ICON});
        markers.push(marker);
    }

    setTimeout(function() {
                   var marker_manager = new MarkerManager(map);
                   marker_manager.addMarkers(markers, 1);
                   marker_manager.refresh();
               }, 0);
}

function cleanupMap()
{
    GUnload();
}

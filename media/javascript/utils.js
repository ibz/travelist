function addTableRow(id, url)
{
    $.get(url, null,
            function(data, status)
            {
                var table = document.getElementById(id);
                var tbody = table.getElementsByTagName("tbody")[0];
                var row = document.createElement("tr");
                var columns = data.split("|");
                for (var i=0; i < columns.length; i++)
                {
                    var column = document.createElement("td");
                    column.innerHTML = "<td>" + columns[i] + "</td>";
                    row.appendChild(column);
                }
                tbody.appendChild(row);
            });
}

function registerContentTypeEvent(selector, name)
{
    $("#id_" + selector).change(
            function()
            {
                var content_type = $("#id_" + selector + " option:selected").eq(0).val();
                if(content_type == "")
                {
                    document.getElementById(name).innerHTML = "";
                }
                $.get("/widget/content_input/?content_type=" + content_type + "&content_type_selector=" + selector + "&name=" + name, null,
                        function(data, status)
                        {
                            document.getElementById(name).innerHTML = data;
                        });
            });
}

function initTripMap(id, point_data)
{
    if (!GBrowserIsCompatible())
    {
        return;
    }

    var initialZoom = 16;

    var map = new GMap2(document.getElementById(id));
    map.addControl(new GLargeMapControl());
    map.setCenter(new GLatLng(0, 0), initialZoom);

    var baseWidth = Math.abs(map.getBounds().getNorthEast().x) * 2;
    var baseHeight = Math.abs(map.getBounds().getNorthEast().y) * 2;

    var points = [];
    var titles = [];

    var minLat = 99999999;
    var minLng = 99999999;
    var maxLat = -99999999;
    var maxLng = -99999999;

    var i;

    for(i = 0; i < point_data.length; i++)
    {
        var lat = point_data[i][0];
        var lng = point_data[i][1];
        var title = point_data[i][2];

        points.push(new GLatLng(lat, lng));
        titles.push(title);

        if(lat < minLat) minLat = lat;
        if(lat > maxLat) maxLat = lat;
        if(lng < minLng) minLng = lng;
        if(lng > maxLng) maxLng = lng;
    }

    var wZoom;
    var w = Math.abs(maxLng - minLng);
    for(wZoom = initialZoom; wZoom >= 0; wZoom--)
    {
        if(baseWidth > w)
        {
            break;
        }
        baseWidth *= 2;
    }

    var hZoom;
    var h = Math.abs(maxLat - minLat);
    for(hZoom = initialZoom; hZoom >= 0; hZoom--)
    {
        if(baseHeight > h)
        {
            break;
        }
        baseHeight *= 2;
    }

    map.setCenter(new GLatLng((minLat + maxLat) / 2, (minLng + maxLng) / 2),
                  (Math.min(wZoom, hZoom)));

    markers = [];
    for(i = 0; i < points.length; i++)
    {
        markers.push(new GMarker(points[i], {title: titles[i]}));
    }

    setTimeout(function() {
                   var mgr = new MarkerManager(map);
                   mgr.addMarkers(markers, 1);
                   mgr.refresh();
                   map.addOverlay(new GPolyline(points, "#ff0000", 10));
               }, 0);
}

function cleanupMap()
{
    GUnload();
}

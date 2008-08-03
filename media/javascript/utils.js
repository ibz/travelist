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
    var markers = [];
    for(var i = 0; i < point_data.length; i++)
    {
        var lat = point_data[i][0];
        var lng = point_data[i][1];
        var title = point_data[i][2];
        markers.push(new GMarker(new GLatLng(lat, lng), {title: title}));
    }
    if (GBrowserIsCompatible()) {
        map = new GMap2(document.getElementById(id));
        map.addControl(new GLargeMapControl());
        map.setCenter(markers[0].getPoint(), 4);
        setTimeout(function() {
                       var mgr = new MarkerManager(map);
                       mgr.addMarkers(markers, 1);
                       mgr.refresh();
                   }, 0);
    }
}

function cleanupMap()
{
    GUnload();
}

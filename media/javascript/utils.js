
function autoCompletePlace(name, id, coords)
{
    $(name).autocomplete("/places/search/",
                         {minChars: 2,
			  matchSubset: false,
			  onItemSelect: function(li) {
			      $(id).attr('value', li.extra[0]);
                              $(name).attr('value', li.extra[1]);
                              if(coords)
                              {
                                  $(coords).attr('value', li.extra[2]);
                              }
                          }});
}

function convertDate(from_format, to_format, date)
{
    function get_format(f)
    {
        if(f == "s")
        {
            return date_format_short;
        }
        else if(f == "l")
        {
            return date_format_long;
        }
        else
        {
            return f;
        }
    }

    if(date == undefined || date == "" || date.toLowerCase() == "none")
    {
        return "";
    }

    return $.datepicker.formatDate(get_format(to_format), $.datepicker.parseDate(get_format(from_format), date));
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

    map.addOverlay(new GPolyline(points, "#ff0000", 3));

    var markers = [];
    for(i = 0; i < points.length; i++)
    {
        markers.push(new GMarker(points[i], {title: titles[i]}));
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

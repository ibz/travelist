function edit_trip()
{
    $("#trip-info").hide();
    $("#trip-info-edit").show();
    $("#trip-info-edit-link").effect('transfer', {to: "#trip-info-edit"}, 500);
    $("#operations").hide();
    $("#trip-info-edit #id_name").focus();
}

function edit_trip_saved(trip_id)
{
    $("#trip-info").show();
    $("#operations").show();
    $("#trip-info-edit").hide();
    update_trip_info(trip_id);
}

function edit_trip_cancel()
{
    $("#trip-info-edit").hide();
    $("#operations").show();
    $("#trip-info").show();
}

function update_trip_details(trip_id)
{
    $("#trip-details").load("/trip/" + trip_id + "/details/");
}

function update_trip_info(trip_id)
{
    function do_update(trip)
    {
        $("#title").html(trip.name);
        $("#trip-info #start-date").html(convertDate("s", "l", trip.start_date));
        $("#trip-info #end-date").html(convertDate("s", "l", trip.end_date));
        $("#trip-info #visibility").html(visibilities[parseInt(trip.visibility)]);
    }
    $.get("/trip/" + trip_id + "/json/", function(data){ do_update(eval("(" + data + ")")); });
}

function edit_points(trip_id)
{
    $("#trip-details").load("/trip/" + trip_id + "/points/");
}

function toggle_annotations(id)
{
    var ul = document.getElementById(id);
    ul.style.display = ul.style.display == 'none' ? 'block' : 'none';
    var a = document.getElementById("link_" + id);
    a.textContent = ul.style.display == 'none' ? "+" : "-";
}

function init_trip(trip_id, has_points)
{
    $("#trip-info-edit > form").ajaxForm({success: function() { edit_trip_saved(trip_id); }});
    $("#trip-info-edit #id_start_date").datepicker({dateFormat: date_format_short});
    $("#trip-info-edit #id_end_date").datepicker({dateFormat: date_format_short});
    update_trip_info(trip_id);
    if(!has_points)
    {
        edit_points(trip_id);
    }
    else
    {
        update_trip_details(trip_id);
    }
}

function init_trip_details(point_data)
{
    $("#trip-details-tabs > ul").tabs();
    initTripMap("map", point_data);
}

function init_trip_new()
{
    $("#trip-info-edit #id_start_date").datepicker({dateFormat: date_format_short});
    $("#trip-info-edit #id_end_date").datepicker({dateFormat: date_format_short});
}

function add_point(point_id, name)
{
    var id = last_id++;
    var li = $("#point-template").clone(true).attr({id: "point_" + id, point_id: point_id, style: ""});
    li.find(".point-name").text(name);
    li.find(".point-delete-link").attr('href', "javascript:delete_point(" + id + ");");
    li.find(".point-edit-link").attr('href', "javascript:edit_point(" + id + ");");
    li.find(".point-edit-save").attr('onclick', "javascript:edit_point_save(" + id + ");");
    li.find(".point-edit-cancel").attr('onclick', "javascript:edit_point_cancel(" + id + ");");
    li.find(".date-arrived,.date-left").datepicker({dateFormat: date_format_short});
    li.find(".visited").attr({id: "visited-" + id});
    li.find(".visited-label").attr({for: "visited-" + id});
    $("#sort-points").append(li);

    return id;
}

function add_new_point()
{
    var name = $("#new-place-name").val();
    var place_id = $("#new-place-id").val();
    var coords = $("#new-place-coords").val().split(",");
    var lat = parseFloat(coords[0]);
    var lng = parseFloat(coords[1]);

    if(place_id == undefined || place_id == "")
    {
        alert("Please fill in the place name.");
        return;
    }

    $("#new-place-name,#new-place-id,#new-place-coords").val("");

    var point_id = "newpoint_" + place_id;
    var id = add_point(point_id, name);
    set_point_data(id, {lat: lat, lng: lng, name: name, date_arrived: "", date_left: "", visited: false}, true);

    refresh_map();

    $("#new-place-name").focus();
}

function edit_point(id)
{
    var point = $("#point_" + id);
    var edit = point.find(".point-edit");
    edit.show();
    point.find(".point-view").effect('transfer', {to: edit}, 500);
    point.addClass("edit-mode");
    var data = points[id];
    edit.find(".date-arrived").val(data.date_arrived);
    edit.find(".date-left").val(data.date_left);
    edit.find(".visited").val(data.visited);
}

function edit_point_save(id)
{
    var point = $("#point_" + id).removeClass("edit-mode");
    var edit = point.find(".point-edit").hide();
    var date_arrived = edit.find(".date-arrived").val();
    var date_left = edit.find(".date-left").val();
    var visited = edit.find(".visited").attr('checked');

    set_point_details(id, date_arrived, date_left, visited);
    set_point_data(id, {date_arrived: date_arrived, date_left: date_left, visited: visited}, true);
}

function edit_point_cancel(id)
{
    $("#point_" + id).removeClass("edit-mode").find(".point-edit").hide();
}

function set_point_details(id, date_arrived, date_left, visited)
{
    var date_arrived_h = convertDate("s", "l", date_arrived);
    var date_left_h = convertDate("s", "l", date_left);
    var details = "";
    if(date_arrived_h != "" || date_left_h != "")
    {
        details = (date_arrived != "" ? date_arrived_h : "?") + " - " + (date_left != "" ? date_left_h : "?");
    }
    if(visited)
    {
        if(details != "")
        {
            details += ", ";
        }
        details += "visited";
    }

    $("#point_" + id).find(".point-details").text(details);
}

function set_point_data(id, dict, modified)
{
    if(!(id in points))
    {
        points[id] = {};
    }
    $.each(dict, function(k, v) { points[id][k] = v; });
    points[id].modified = modified;
}

function delete_point(id)
{
    $("#point_" + id).remove();
    refresh_map();
}

function trip_points_save(trip_id)
{
    var point_strs = $.map($("#sort-points").sortable('toArray'),
                           function(id)
                           {
                               var point = points[parseInt(id.substr(id.indexOf("_") + 1))];
                               var point_str = "id=" + $("#" + id).attr("point_id");
                               if(point.modified)
                               {
                                   point_str += ",";
                                   point_str += "date_arrived=" + point.date_arrived + ",";
                                   point_str += "date_left=" + point.date_left + ",";
                                   point_str += "visited=" + (point.visited ? 1 : 0);
                               }
                               return point_str;
                            });

    $.post("/trip/" + trip_id + "/points/",
           {points: point_strs.join(";")},
           function(data) { update_trip_details(trip_id); });
}

function trip_points_cancel(trip_id)
{
    update_trip_details(trip_id);
}

function init_trip_points(point_data)
{
    $("#sort-points").sortable({revert: true, placeholder: "ui-placeholder", update: function(){ refresh_map(); }});
    autoCompletePlace("#new-place-name", "#new-place-id", "#new-place-coords");
    for(var i = 0; i < point_data.length; i++)
    {
      var id = add_point("oldpoint_" + point_data[i].id, point_data[i].name);
        set_point_details(id, point_data[i].date_arrived, point_data[i].date_left, point_data[i].visited);
        set_point_data(id, point_data[i], false);
    }
    refresh_map();
}

function refresh_map()
{
    var point_data = $.map($("#sort-points").sortable('toArray'),
                           function(id)
                           {
                               var point = points[parseInt(id.substr(id.indexOf("_") + 1))];
                               return [[point.lat, point.lng, point.name]];
                           });
    initTripMap("map", point_data);
}
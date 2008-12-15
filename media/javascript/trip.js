function update_trip_details(trip_id)
{
    $("#trip-details").load("/trips/" + trip_id + "/details/");
}

function edit_points(trip_id)
{
    $("#trip-details").load("/trips/" + trip_id + "/points/");
}

function suggest_place()
{
    $("#suggest-place").show();
    $("#add-place,#suggest-place-message").hide();
}

function suggest_place_ok()
{
    var name = $("#suggest-name").val();
    var comments = $("#suggest-comments").val();
    if (!name || !comments)
    {
        alert("Please fil in the place name and comments!");
        return;
    }
    $("#suggest-buttons").hide();
    $("#suggest-activity").show();
    $.ajax({
        type: "POST",
        url: "/places/suggest/",
        data: "name=" + name + "&comments=" + comments,
        success: function()
        {
            $("#suggest-name,#suggest-comments").val("");
            $("#suggest-place").hide();
            $("#add-place,#suggest-place-message").show();
            $("#suggest-buttons").show();
            $("#suggest-activity").hide();
        },
        error: function()
        {
            $("#suggest-buttons").show();
            $("#suggest-activity").hide();
        }});
}

function suggest_place_cancel()
{
    $("#suggest-place").hide();
    $("#add-place,#suggest-place-message").show();
}

function toggle_annotations(id)
{
    var ul = document.getElementById(id);
    ul.style.display = ul.style.display == 'none' ? 'block' : 'none';
    var a = document.getElementById("link_" + id);
    a.textContent = ul.style.display == 'none' ? "+" : "-";
}

function delete_annotation(trip_id, id)
{
    if(!confirm("Are you sure you want to delete this annotation?"))
    {
        return;
    }
    $.post("/trips/" + trip_id + "/annotations/" + id + "/delete/", {},
           function()
           {
               $("#trip-details-tabs #annotation_" + id).remove();
           });
}

function delete_trip(id)
{
    if(!confirm("You will lose all the data associated with this trip and there is no way to undo this operation. Really continue?"))
    {
        return;
    }
    $.post("/trips/" + id + "/delete/", {},
           function()
           {
               window.location = "/";
           });
}

function init_trip(trip_id, has_points, allow_edit)
{
    $("#trip-info-edit > form").ajaxForm({success: function() { edit_trip_saved(trip_id); }});
    $("#trip-info-edit #id_start_date").datepicker({dateFormat: date_format_short});
    $("#trip-info-edit #id_end_date").datepicker({dateFormat: date_format_short});
    if(!has_points)
    {
        if(allow_edit)
        {
            edit_points(trip_id);
        }
        else
        {
            $("#map").hide();
        }
    }
    else
    {
        update_trip_details(trip_id);
    }
}

function init_trip_details(point_data)
{
    $("#trip-details-tabs > ul").tabs();
    $("#trip-details-tabs .annotation").hover(function() { $(this).addClass('hover'); }, function() { $(this).removeClass('hover'); });
    initTripMap("map", point_data);
}

function init_trip_new()
{
    $("form#trip-info #id_start_date").datepicker({dateFormat: date_format_short});
    $("form#trip-info #id_end_date").datepicker({dateFormat: date_format_short});
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
    var view = point.find(".point-view");
    var edit = point.find(".point-edit");
    edit.show();
    view.find(".operations").hide();
    view.effect('transfer', {to: edit}, 500);
    point.addClass("edit-mode");
    var data = points[id];
    edit.find(".date-arrived").val(data.date_arrived);
    edit.find(".date-left").val(data.date_left);
    edit.find(".visited").val(data.visited);
}

function edit_point_save(id)
{
    var point = $("#point_" + id).removeClass("edit-mode");
    var edit = point.find(".point-edit");
    var date_arrived = edit.find(".date-arrived").val();
    var date_left = edit.find(".date-left").val();
    var visited = edit.find(".visited").attr('checked');
    point.find(".point-view .operations").show();
    edit.hide();
    set_point_details(id, date_arrived, date_left, visited);
    set_point_data(id, {date_arrived: date_arrived, date_left: date_left, visited: visited}, true);
}

function edit_point_cancel(id)
{
    var point = $("#point_" + id);
    point.removeClass("edit-mode");
    point.find(".point-view .operations").show();
    point.find(".point-edit").hide();
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

    $.post("/trips/" + trip_id + "/points/",
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

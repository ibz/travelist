var current_trip; // JS global variable

function update_trip_details(trip_id)
{
    var activity = $("#trip-activity");
    activity.show();
    $("#trip-details").load("/trips/" + trip_id + "/details/", null,
                            function() { activity.hide(); });
}

function edit_points(trip_id)
{
    var activity = $("#trip-activity");
    activity.show();
    $("#trip-details").empty().load("/trips/" + trip_id + "/points/", null,
                                    function() { activity.hide(); });
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
        alert("Please fill in the place name and comments!");
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

function delete_annotation(trip_id, id)
{
    if(!confirm("Are you sure you want to delete this annotation?"))
    {
        return;
    }
    $.post("/trips/" + trip_id + "/annotations/" + id + "/delete/", {},
           function()
           {
               window.location = "/trips/" + trip_id + "/";
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

function init_trip(trip, has_points, allow_edit)
{
    if(!has_points)
    {
        if(allow_edit)
        {
            edit_points(trip.id);
        }
        else
        {
            $("#map").hide();
        }
    }
    else
    {
        update_trip_details(trip.id);
    }

    current_trip = trip;
}

function init_trip_details(point_data)
{
    $("#trip-details-tabs").tabs();
    $(".annotation").hover(function() { $(this).addClass('hover'); }, function() { $(this).removeClass('hover'); });
    initTripMap(point_data, true);
}

function init_trip_edit()
{
    $("form#trip-info #id_start_date").datepicker({onSelect: function(dateText) { changeDefaultDate("form#trip-info #id_end_date", dateText); }});
    $("form#trip-info #id_end_date").datepicker();
}

function fix_point_dates() // enable / disable date editor for points, depending on whether they are terminal points ot not
{
    var children = $("#sort-points").children();
    function terminal(i, date_arrived_enabled, date_left_enabled) {
        var id = $(children[i]).attr('id');
        id = parseInt(id.substr(id.indexOf("_") + 1));
        set_point_data(id, {date_arrived: date_arrived_enabled ? points[id].date_arrived : "",
                            date_left: date_left_enabled ? points[id].date_left : ""}, true);
        $(children[i]).find(".date-arrived").attr('disabled', !date_arrived_enabled).val(points[id].date_arrived);
        $(children[i]).find(".date-left").attr('disabled', !date_left_enabled).val(points[id].date_left);
    }
    $.each(children, function(i, val) {
               if (i == 0) {
                   terminal(i, false, true);
               } else if (i == children.length - 1) {
                   terminal(i, true, false);
               }
               else {
                   $(children[i]).find(".date-arrived,.date-left").attr('disabled', false);
               }
           });
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
    li.find(".date-arrived,.date-left").datepicker({defaultDate: parseDate("s", current_trip.start_date)});
    li.find(".date-arrived").datepicker('option', 'onSelect', function(dateText) { changeDefaultDate(li.find(".date-left"), dateText); });
    li.find(".visited").attr('id', "visited-" + id);
    li.find(".visited-label").attr('for', "visited-" + id);
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
    set_point_data(id, {lat: lat, lng: lng, name: name, date_arrived: "", date_left: "", visited: false, place_id: place_id}, true);
    edit_point(id);

    refresh_map();
    fix_point_dates();

    $("#new-place-name").focus();
}

function edit_point(id)
{
    var point = $("#point_" + id);
    var view = point.find(".point-view");
    var edit = point.find(".point-edit");
    var is_new = point.attr('point_id').indexOf('newpoint') == 0;
    edit.show();
    view.effect('transfer', {to: edit}, 500);
    point.addClass("edit-mode");
    var data = points[id];
    edit.find(".date-arrived").val(data.date_arrived);
    edit.find(".date-left").val(data.date_left);
    edit.find(".visited").attr('checked', data.visited);
    if(is_new)
    {
        edit.find(".operations").hide();
        view.find(".operations .point-edit-link").hide();
    }
    else
    {
        view.find(".operations").hide();
    }
}

function edit_point_save_data(id)
{
    var point = $("#point_" + id);
    var edit = point.find(".point-edit");
    var date_arrived = edit.find(".date-arrived").val();
    var date_left = edit.find(".date-left").val();
    var visited = edit.find(".visited").attr('checked');
    set_point_data(id, {date_arrived: date_arrived, date_left: date_left, visited: visited}, true);
}

function edit_point_save(id)
{
    edit_point_save_data(id);
    var point = $("#point_" + id);
    var edit = point.find(".point-edit");
    point.removeClass("edit-mode");
    point.find(".point-view .operations").show();
    edit.hide();

    refresh_map();
}

function edit_point_cancel(id)
{
    var point = $("#point_" + id);
    point.removeClass("edit-mode");
    point.find(".point-view .operations").show();
    point.find(".point-edit").hide();
}

function set_point_data(id, dict, modified)
{
    if(!(id in points))
    {
        points[id] = {};
    }
    $.each(dict, function(k, v) { points[id][k] = v; });
    points[id].modified = modified;

    // update the dates displayed, if necessary
    if('date_arrived' in dict || 'date_left' in dict)
    {
        var li = $("#point_" + id);

        var date_arrived_h = convertDate("s", "l", points[id].date_arrived);
        var date_left_h = convertDate("s", "l", points[id].date_left);

        if(date_arrived_h != "" || date_left_h != "")
        {
            if (date_arrived_h == "" && !(li.prev('li').length == 0))
            {
                date_arrived_h = "?";
            }
            if (date_left_h == "" && !(li.next('li').length == 0))
            {
                date_left_h = "?";
            }
        }

        li.find(".point-details").text($.grep([date_arrived_h, date_left_h], function(d) { return d != ""; }).join(" - "));
    }
}

function delete_point(id)
{
    $("#point_" + id).remove();
    refresh_map();
    fix_point_dates();
}

function trip_points_save(trip_id)
{
    var point_strs = $.map($("#sort-points").sortable('toArray'),
                           function(id)
                           {
                               id = parseInt(id.substr(id.indexOf("_") + 1));
                               var point_id = $("#point_" + id).attr("point_id");
                               var is_new = point_id.indexOf('newpoint') == 0;
                               if(is_new)
                               {
                                   edit_point_save_data(id);
                               }
                               var point = points[id];
                               var point_str = "id=" + point_id;
                               if(point.modified)
                               {
                                   point_str += ",";
                                   point_str += "date_arrived=" + point.date_arrived + ",";
                                   point_str += "date_left=" + point.date_left + ",";
                                   point_str += "visited=" + (point.visited ? 1 : 0);
                               }
                               return point_str;
                            });
    var default_transportation = $("#default_transportation").val();

    $.post("/trips/" + trip_id + "/points/",
           {points: point_strs.join(";"), default_transportation: default_transportation || ""},
           function(data) { update_trip_details(trip_id); });
}

function trip_points_cancel(trip_id)
{
    update_trip_details(trip_id);
}

function init_trip_points(point_data)
{
    $("#sort-points").sortable({revert: true, placeholder: "ui-placeholder",
                                // Don't know why I need this, but sorting edit-mode points will mess up list after edit ends if I don't have it :)
                                stop: function() {$('#sort-points > li').attr('style', null); },
                                update: function(){ refresh_map(); fix_point_dates(); }});
    autoCompletePlace("#new-place-name", "#new-place-id", "#new-place-coords");
    for(var i = 0; i < point_data.length; i++)
    {
      var id = add_point("oldpoint_" + point_data[i].id, point_data[i].name);
        set_point_data(id, point_data[i], false);
    }
    refresh_map();
    fix_point_dates();
}

function refresh_map()
{
    var point_data = $.map($("#sort-points").sortable('toArray'),
                           function(id)
                           {
                               var p = points[parseInt(id.substr(id.indexOf("_") + 1))];
                               return [{lat:p.lat, lng:p.lng, name:p.name, id:p.id, date_arrived:p.date_arrived, date_left:p.date_left, visited:p.visited, place_id:p.place_id}];
                           });
    initTripMap(point_data, false);
}

function transportation_edit(link, annotation_id)
{
    var annotation = $(link).closest(".annotation");

    // select box
    var select = document.createElement('select');
    $(select).html($.map(TRANSPORTATION_CHOICES, function(t) { return "<option value=\"" + t[0] + "\">" + t[1] + "</option>"; }).join(""));
    $(select).val(annotation.find(".content span").attr('data-id'));
    annotation.find(".content").empty().append(select);

    // save button
    var button = document.createElement('button');
    $(button).attr({type: 'button', 'class': 'positive'}).html("Save");
    var editLink = annotation.find(".operations a").replaceWith(button);

    // class
    annotation.find(".operations").attr('class', 'edit-operations');

    button.onclick = function()
    {
        function success(data)
        {
            // redo class
            annotation.find(".edit-operations").attr('class', 'operations');

            // redo save button
            annotation.find(".operations button").replaceWith(editLink);

            // redo select box
            var id = parseInt(eval(data)[0].fields.content);
            var transportation = $.grep(TRANSPORTATION_CHOICES, function(t) { return t[0] == id; })[0];
            var content = "Transportation: <span data-id=\"" + transportation[0] + "\">" + transportation[1] + "</span>";
            annotation.find(".content").empty().append(content);

            // change marker
            var marker = transportation_markers[annotation_id];
            if (marker)
            {
                marker.setImage(id ? "/media/images/transportation/" + id + ".png" : null);
                if (id)
                {
                    marker.show();
                }
                else
                {
                    marker.hide();
                }
            }

            // need to change the annotation from segment-data too, since that it will be used the next time the balloon is opened
            var annotation_p = $("#segment-data " + annotation.closest(".short-content").attr('data-path')).find("#annotation-" + annotation_id);
            annotation_p.find(".content").empty().append(content);
        }
        $.post("/trips/" + current_trip.id + "/annotations/" + annotation_id + "/edit/", {content: TRANSPORTATION_CHOICES[select.selectedIndex][0]}, success);
    };
}

function add_links()
{
    $("#existing-links").hide();
    $("#add-links #users").empty();
    $("#add-links").show();
}

function add_links_invite()
{
    var user_ids = $.map($("#add-links #users .user-id"), function (el) { return $(el).val(); }).join(",");
    if (!user_ids || user_ids == "")
    {
        alert("Add at least one friend before clicking invite.");
        return;
    }
    var activity = $("#trip-activity");
    var buttons = $("#add-links #invite,#add-links #cancel");
    activity.show();
    buttons.hide();
    $.post("/trips/" + current_trip.id + "/links/new/", {user_ids: user_ids}, function() { $("#add-links").hide(); $("#existing-links").show(); buttons.show(); activity.hide(); });
}

function add_links_cancel()
{
    $("#add-links").hide();
    $("#existing-links").show();
}

function add_new_user()
{
    if (!$("#add-links #new-user").val())
    {
        alert("Select a friend from the list.");
        return;
    }
    var li = document.createElement('li');
    $(li).append($("#add-links #new-user :selected").text());
    var hidden = document.createElement('input');
    $(hidden).attr({type: 'hidden', 'class': 'user-id'});
    $(hidden).val($("#add-links #new-user").val());
    $(li).append(hidden);
    $("#add-links #users").append(li);
}

function delete_link(link_id, username)
{
    if(!confirm("Are you sure you want to remove " + username + " from your trip?"))
    {
        return;
    }
    $.post("/trips/" + current_trip.id + "/links/" + link_id + "/delete/", {},
           function()
           {
               window.location = "/trips/" + current_trip.id + "/";
           });
}

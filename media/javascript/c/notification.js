function notification_list_init()
{
    $(".dialog").dialog({autoOpen: false,
                         modal: true,
                         buttons: {"OK": function() {
                                       var self = $(this);
                                       perform_action(parseInt(self.attr('data-id')), parseInt(self.attr('data-action_id')), function() { self.dialog('close'); });
                                   },
                                   "Cancel": function() { $(this).dialog('close'); }}
                        });
}

function dispatch_action(id, action_id, action_name)
{
    if($("#dialog-" + id).hasClass("action-" + action_name))
    {
        $("#dialog-" + id).attr({'data-id': id, 'data-action_id': action_id}).dialog('open');
    }
    else
    {
        perform_action(id, action_id);
    }
}

function data_TRIP_LINK_REQUEST(id)
{
    var link_type = $("input[name='link-type-" + id + "']:checked").val();
    var start_place = link_type == 'whole' ? null : $(".select-places-" + id + " .start-place").val();
    var end_place = link_type == 'whole' ? null : $(".select-places-" + id + " .end-place").val();
    var copy_status = $("input[name='copy-status-" + id + "']:checked").val();
    var link_to_trip = copy_status == 'copy' ? null : $(".select-trip-" + id + " .link-to-trip").val();

    if (copy_status != 'copy' && link_to_trip == "")
    {
        alert("Please select the corresponding trip.");
        return null;
    }

    return {link_type: link_type, start_place: start_place, end_place: end_place, copy_status: copy_status, link_to_trip: link_to_trip};
}

function perform_action(id, action_id, callback)
{
    var notification_type = $("#notification-" + id).attr('data-notification_type');

    var data = eval("typeof data_" + notification_type) == 'function' ? eval("data_" + notification_type)(id) : { };
    if(!data)
    {
        return;
    }

    data['action_id'] = action_id;
    $.post("/notifications/" + id + "/", data,
           function()
           {
               if(callback)
               {
                   callback();
               }
               $("#notification-" + id).remove();
               if($("#notification-list").children().size() == 0)
               {
                   window.location = "/";
               }
           });
}

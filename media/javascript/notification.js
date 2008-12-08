function perform_action(id, action_id)
{
    $.post("/notifications/" + id + "/", {action_id: action_id},
         function() { $("#notification_" + id).remove(); });
}

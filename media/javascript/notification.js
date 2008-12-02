function perform_action(id, action_id)
{
  $.post("/notification/" + id + "/action/" + action_id + "/", {},
         function() { $("#notification_" + id).remove(); });
}

function delete_comment(place_id, id)
{
    if(!confirm("Are you sure you want to delete this comment?"))
    {
        return;
    }
    $.post("/places/" + place_id + "/comments/" + id + "/delete/", {},
           function()
           {
               window.location = "/places/" + place_id + "/"; // TODO: this URL doesn't include the place name
           });
}
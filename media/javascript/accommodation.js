function delete_comment(accommodation_id, id)
{
    if(!confirm("Are you sure you want to delete this comment?"))
    {
        return;
    }
    $.post("/accommodations/" + accommodation_id + "/comments/" + id + "/delete/", {},
           function()
           {
               window.location = "/accommodations/" + accommodation_id + "/"; // TODO: this URL doesn't include the accommodation name
           });
}
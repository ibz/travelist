function update_new_annotation_link(trip_id, tab_index)
{
    var content_type_id = content_types_list[tab_index];
    $("#new-annotation-link").attr({href: "/trips/" + trip_id + "/annotations/new/?content_type=" + content_type_id});
    $("#new-annotation-link").text("add new " + content_types[content_type_id]);
}

function init_annotation_list(trip_id)
{
  $("#annotation-tabs > ul").tabs().bind('tabsselect', function(event, ui) { update_new_annotation_link(trip_id, ui.index); });
    update_new_annotation_link(trip_id, $("#annotation-tabs > ul").tabs().data('selected.tabs'));
}

function init_annotation_edit()
{
    $("#annotation-info-edit #id_date").datepicker({dateFormat: date_format_short});
}

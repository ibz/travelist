function init_annotation_edit()
{
    $("#annotation-info-edit #id_date").datepicker({dateFormat: date_format_short});
}

function accomodation_toggle_contact()
{
    $("#accomodation-contact").toggle();
}

function accomodation_toggle_rating()
{
    $("#accomodation-rating").toggle();
}
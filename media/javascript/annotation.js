function init_annotation_edit()
{
    $("#annotation-info-edit #id_date").datepicker({dateFormat: date_format_short});
}

function init_annotation_edit_transportation(classes, class_mapping, selected_class)
{
    $("#id_content_means").change(function()
                                  {
                                      var means = $("#id_content_means option:selected").val();
                                      $("#id_content_class").empty();
                                      $("#id_content_class").append("<option value=\"0\"></option>");
                                      var child_added = false;
                                      if (class_mapping[means] != undefined)
                                      {
                                          for(var i = 0; i < class_mapping[means].length; i++)
                                          {
                                              $("#id_content_class").append("<option value=\"" + class_mapping[means][i] + "\">" + classes[class_mapping[means][i]] + "</option>");
                                              child_added = true;
                                          }
                                      }
                                      if(!child_added)
                                      {
                                          $("#content_class").hide();
                                      }
                                      else
                                      {
                                          $("#content_class").show();
                                          $("#id_content_class").val(selected_class);
                                      }
                                  }).change();
}

function accomodation_toggle_contact()
{
    $("#accomodation-contact").toggle();
}

function accomodation_toggle_rating()
{
    $("#accomodation-rating").toggle();
}
function init_annotation_edit()
{
    $("#annotation-info-edit #id_date").datepicker({dateFormat: date_format_short});
}

function init_annotation_edit_transportation(classes, class_mapping, number_mapping, selected_class)
{
    $("#id_content_means").change(
        function()
        {
            var means = $("#id_content_means option:selected").val();
            if ($.inArray(parseInt(means), number_mapping) != -1)
            {
                $("#content_number").show();
            }
            else
            {
                $("#content_number").hide();
                $("#id_content_number").val("");
            }
            var select_class_e = $("#id_content_class");
            select_class_e.empty().append("<option value=\"0\"></option>");
            var child_added = false;
            if (class_mapping[means] != undefined)
            {
                for(var i = 0; i < class_mapping[means].length; i++)
                {
                    select_class_e.append("<option value=\"" + class_mapping[means][i] + "\">" + classes[class_mapping[means][i]] + "</option>");
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
                select_class_e.val(selected_class);
            }
        }).change();
}

function accommodation_add()
{
    var name = prompt("Name", "");
    $("#id_content").addOption(name, name).selectOptions(name);
}

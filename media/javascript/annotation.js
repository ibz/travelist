function accommodation_add()
{
    var name = prompt("Name", "");
    $("#id_content").addOption(name, name).selectOptions(name);
}

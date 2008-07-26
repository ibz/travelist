function addListItem(id, url)
{
    $.get(url, null,
            function(data, status)
            {
                var list = document.getElementById(id);
                var item = document.createElement("li");
                item.innerHTML = "<li>" + data + "</li>";
                list.appendChild(item);
            });
}

function registerContentTypeEvent(selector, name)
{
    $("#id_" + selector).change(
            function()
            {
                var content_type = $("#id_" + selector + " option:selected").eq(0).val();
                if(content_type == "")
                {
                    document.getElementById(name).innerHTML = "";
                }
                $.get("/widget/content_input/?content_type=" + content_type + "&content_type_selector=" + selector + "&name=" + name, null,
                        function(data, status)
                        {
                            document.getElementById(name).innerHTML = data;
                        });
            });
}

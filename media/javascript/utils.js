function addTableRow(id, url)
{
    $.get(url, null,
            function(data, status)
            {
                var table = document.getElementById(id);
                var tbody = table.getElementsByTagName("tbody")[0];
                var row = document.createElement("tr");
                var columns = data.split("|");
                for (var i=0; i < columns.length; i++)
                {
                    var column = document.createElement("td");
                    column.innerHTML = "<td>" + columns[i] + "</td>";
                    row.appendChild(column);
                }
                tbody.appendChild(row);
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

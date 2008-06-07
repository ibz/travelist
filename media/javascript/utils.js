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

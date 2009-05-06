function autoCompletePlace(name, id, coords)
{
    $(name).autocomplete("/places/search/",
                         {minChars: 2,
                          matchSubset: false,
                          cacheLength: 0,
                          onItemSelect: function(li) {
			                  $(id).attr('value', li.extra[0]);
                              $(name).attr('value', li.extra[1]);
                              if(coords)
                              {
                                  $(coords).attr('value', li.extra[2]);
                              }
                          }});
}

function convertDate(from_format, to_format, date)
{
    function get_format(f)
    {
        if(f == "s")
        {
            return date_format_short;
        }
        else if(f == "l")
        {
            return date_format_long;
        }
        else
        {
            return f;
        }
    }

    if(date == undefined || date == "" || date.toLowerCase() == "none")
    {
        return "";
    }

    return $.datepicker.formatDate(get_format(to_format), $.datepicker.parseDate(get_format(from_format), date));
}

function ordinal(n) {
    return n + (
        (n % 10 == 1 && n % 100 != 11) ? "st" :
        (n % 10 == 2 && n % 100 != 12) ? "nd" :
        (n % 10 == 3 && n % 100 != 13) ? "rd" : "th");
}

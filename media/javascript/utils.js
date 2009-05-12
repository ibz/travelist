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

function _getDateFormat(f)
{
    return f == "s" ? DATE_FORMAT_SHORT : f == "l" ? DATE_FORMAT_LONG : f;
}

function parseDate(format, date)
{
    return !date || date == "" ? null : $.datepicker.parseDate(_getDateFormat(format), date);
}

function formatDate(format, date)
{
    return !date ? "" : $.datepicker.formatDate(_getDateFormat(format), date);
}

function convertDate(from_format, to_format, date)
{
    return formatDate(to_format, parseDate(from_format, date));
}

function changeDefaultDate(pickerSelector, dateText)
{
    $(pickerSelector).datepicker('option', 'defaultDate', parseDate("s", dateText));
}

function ordinal(n) {
    return n + (
        (n % 10 == 1 && n % 100 != 11) ? "st" :
        (n % 10 == 2 && n % 100 != 12) ? "nd" :
        (n % 10 == 3 && n % 100 != 13) ? "rd" : "th");
}

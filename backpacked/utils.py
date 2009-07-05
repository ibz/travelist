import re
import sys
import unicodedata
from datetime import datetime
from functools import update_wrapper

from django import template

import settings

def find(l, func):
    for item in l:
        if func(item):
            return item

def format_date(value):
    if not value:
        return ""
    return value.strftime(settings.DATE_FORMAT_SHORT_PY)

def parse_date(s):
    if not s:
        return None
    for format in [settings.DATE_FORMAT_SHORT_PY,
                   settings.DATE_TIME_FORMAT_SHORT_PY,
                   "%s %s" % (settings.DATE_FORMAT_SHORT_PY, settings.TIME_FORMAT_LONG_PY)]:
        try:
            return datetime.strptime(s, format)
        except ValueError:
            continue
        except:
            raise

def format_date_human(value):
    return template.defaultfilters.date(value)

def format_datetime_human(value):
    return "%s %s" % (template.defaultfilters.date(value), template.defaultfilters.time(value))

class Enum:
    def __init__(self, all):
        """
            'all' is either a dict that looks like this:
            {'MEMBER_NAME_1': (1, "Member description 1", ...),
             'MEMBER_NAME_2': (2, "Member description 2", ...), ...}
            or a list that looks like this:
            [(1, "Member 1", ...),
             (2, "Member 2", ...), ...]
        """
        if isinstance(all, dict):
            self.all = all
        else:
            name = lambda desc: re.sub("[^A-Z0-9_]", "X", re.sub(" ", "_", desc.upper()))
            self.all = dict((name(e[1]), e) for e in all)
        self.all_by_value = dict((i[1][0], (i[0],) + i[1][1:]) for i in self.all.items())

    def __getattr__(self, name):
        return self.all[name][0]

    def __call__(self, value):
        value = int(value)
        if value not in self.values:
            raise ValueError()
        return value

    @property
    def choices(self):
        return sorted(self.all.values(), key=lambda c: c[0])

    @property
    def items(self):
        return self.all.keys()

    @property
    def values(self):
        return self.all_by_value.keys()

    def get_description(self, value):
        return self.all_by_value[value][1]

    def get_extra(self, value):
        return self.all_by_value[value][2:]

    def get_name(self, value):
        return self.all_by_value[value][0]

def cached_property(func):
    def _get(self):
        try:
            return self.__dict__[func.__name__]
        except KeyError:
            value = func(self)
            self.__dict__[func.__name__] = value
            return value
    update_wrapper(_get, func)
    def _del(self):
        del self.__dict__[func.__name__]
    return property(_get, None, _del)

class UnicodeASCIIMap(dict):
    """
    Maps a unicode character code to a replacement code or a unicode string.
    """

    STATIC_MAP = {
        # characters that don't have a unicode decomposition
        0xe6: u"ae", # LATIN SMALL LETTER AE
        0xc6: u"AE", # LATIN CAPITAL LETTER AE
        0xf0: u"d",  # LATIN SMALL LETTER ETH
        0xd0: u"D",  # LATIN CAPITAL LETTER ETH
        0xf8: u"oe", # LATIN SMALL LETTER O WITH STROKE
        0xd8: u"OE", # LATIN CAPITAL LETTER O WITH STROKE
        0xfe: u"th", # LATIN SMALL LETTER THORN
        0xde: u"Th", # LATIN CAPITAL LETTER THORN
        0xdf: u"ss", # LATIN SMALL LETTER SHARP S
    }

    def __missing__(self, k):
        if k in self:
            return self[k]
        v = k
        if k in self.STATIC_MAP:
            v = self.STATIC_MAP[k]
        else:
            de = unicodedata.decomposition(unichr(k))
            if de:
                try:
                    v = int(de.split(None, 1)[0], 16)
                except (IndexError, ValueError):
                    pass
        self[k] = v
        return v
UnicodeASCIIMap = UnicodeASCIIMap()

def human_unicode_to_ascii(s):
    return unicode(s).translate(UnicodeASCIIMap).encode("ascii", "ignore")

title_for_url_filters = [(re.compile(f[0]), f[1]) for f in [(r"[^a-z0-9-\ ]", ""), (r" ", "-"), (r"-+", "-"), (r"(^-)|(-$)", "")]]
def clean_title_for_url(title):
    title = human_unicode_to_ascii(title).lower()
    for filter in title_for_url_filters:
        title = filter[0].sub(filter[1], title)
    return title

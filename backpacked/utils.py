import re
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
        return sorted(self.all.values(), lambda lhs, rhs: cmp(lhs[0], rhs[0]))

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

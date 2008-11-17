from datetime import datetime

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
        if isinstance(all, dict):
            self.all = all
        else:
            self.all = dict((e[1].upper(), e) for e in all)

    def __getattr__(self, name):
        return self.all[name][0]

    @property
    def choices(self):
        return sorted(self.all.values(), lambda lhs, rhs: cmp(lhs[0], rhs[0]))

    @property
    def items(self):
        return self.all.keys()

    @property
    def values(self):
        return [v[0] for v in self.all.values()]

    def get_description(self, value):
        for i in self.choices:
            if i[0] == value:
                return i[1]

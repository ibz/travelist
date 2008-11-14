from datetime import datetime

from django.template import defaultfilters

import settings

def find(l, func):
    for item in l:
        if func(item):
            return item

def format_date(value):
    return value.strftime(settings.DATE_FORMAT_SHORT_PY)

def parse_date(s):
    if not s:
        return None
    return datetime.strptime(s, settings.DATE_FORMAT_SHORT_PY)

def format_date_human(value):
    return defaultfilters.date(value)

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

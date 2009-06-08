import os

from django import template

import settings

register = template.Library()

class CachedFileNode(template.Node):
    def __init__(self, path):
        self.path = path

    def render(self, context):
        path = self.path.resolve(context)

        if settings.DEBUG:
            return path

        version = None
        f = open("%s.v" % os.path.join(settings.MEDIA_ROOT, path))
        try:
            version = f.readline()
        finally:
            f.close()
        assert version and len(version) == 8

        file, ext = os.path.splitext(path)

        return "".join([file, ".v-%s" % version, ".min", ext])

def do_call(parser, token):
    path = parser.compile_filter(token.contents.split(" ", 1)[1])
    return CachedFileNode(path)

register.tag('cachedfile', do_call)

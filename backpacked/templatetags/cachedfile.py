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

        versionfile = "%s.v" % os.path.join(settings.MEDIA_ROOT, path)

        if not os.path.exists(versionfile):
            return path

        version = None
        f = open(versionfile)
        try:
            version = f.readline()
        except:
            pass
        finally:
            f.close()

        if not version:
            return path

        file, ext = os.path.splitext(path)
        newpath = "".join([file, ".v-%s" % version, ext])

        return newpath

def do_call(parser, token):
    path = parser.compile_filter(token.contents.split(" ", 1)[1])
    return CachedFileNode(path)

register.tag('cachedfile', do_call)

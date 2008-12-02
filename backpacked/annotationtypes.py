import os
import subprocess
from tempfile import mkdtemp

from django.utils import html
from django.utils import safestring

from django import http
from django import forms

from backpacked import models
from backpacked import utils
from backpacked import views

import settings

def get_manager(content_type):
    return AnnotationManager.all[content_type]

class AnnotationManager(object):
    all = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, classdict):
            type.__init__(cls, name, bases, classdict)
            if hasattr(cls, 'content_type'):
                AnnotationManager.all[cls.content_type] = cls

    title_required = True

    trip_allowed = True
    point_allowed = True
    segment_allowed = True

    has_extended_content = False
    edit_content_as_file = False

    user_levels = models.UserLevel.values

    is_photos = False

    def __init__(self, annotation):
        self.annotation = annotation

    def render_short(self):
        raise NotImplementedError()

    def render(self, request):
        raise NotImplementedError()

    def render_content_input(self, name, value, attrs=None):
        raise NotImplementedError()

    def clean_content(self, content):
        raise NotImplementedError()

    def after_save(self):
        pass

class TextAnnotationManager(AnnotationManager):
    content_type = models.ContentType.TEXT

    has_extended_content = True

    def render_short(self):
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.url),
                                                               html.escape(self.annotation.title)))

    def render(self, request):
        return views.render("annotation_view_text.html", request, {'annotation': self.annotation})

    def render_content_input(self, name, value, attrs=None):
        return forms.widgets.Textarea().render(name, value, attrs)

    def clean_content(self, content):
        return content

class UrlAnnotationManager(AnnotationManager):
    content_type = models.ContentType.URL

    def render_short(self):
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.content),
                                                               html.escape(self.annotation.title)))

    def render_content_input(self, name, value, attrs=None):
        return forms.widgets.TextInput().render(name, value, attrs)

    def clean_content(self, content):
        return forms.fields.URLField().clean(content)

class ExternalPhotosAnnotationManager(UrlAnnotationManager):
    content_type = models.ContentType.EXTERNAL_PHOTOS

    is_photos = True

Transportation = utils.Enum([(0, "Unspecified"),
                             (1, "Airplane"),
                             (2, "Bike"),
                             (3, "Boat"),
                             (4, "Bus"),
                             (5, "Car"),
                             (6, "Motorcycle"),
                             (7, "Train"),
                             (8, "Walk")])

class TransportationAnnotationManager(AnnotationManager):
    content_type = models.ContentType.TRANSPORTATION

    exclude_fields = ('title', 'date')

    title_required = False

    trip_allowed = False
    point_allowed = False

    def render_short(self):
        return "Transportation: %s" % Transportation.get_description(int(self.annotation.content))

    def render_content_input(self, name, value, attrs=None):
        return forms.widgets.Select(choices=Transportation.choices).render(name, value, attrs)

    def clean_content(self, content):
        return str(forms.fields.ChoiceField(choices=Transportation.choices).clean(content))

class GPSAnnotationManager(AnnotationManager):
    content_type = models.ContentType.GPS

    title_required = False

    user_levels = [models.UserLevel.PRO]

    has_extended_content = True
    edit_content_as_file = True

    def get_cache_filename(self):
        if self.annotation.id:
            return os.path.join(settings.GPS_ANNOTATION_CACHE_PATH, "%s.kmz" % self.annotation.id)
        else:
            return None

    def ensure_cache_file(self):
        cachefilename = self.get_cache_filename()
        assert cachefilename

        if os.path.exists(cachefilename):
            return

        tempdir = mkdtemp()
        gpxfilename = os.path.join(tempdir, "doc.gpx")
        kmlfilename = os.path.join(tempdir, "doc.kml")
        kmzfilename = os.path.join(tempdir, "doc.kmz")
        try:
            gpxfile = file(gpxfilename, "w")
            try:
                gpxfile.write(self.annotation.extended_content.content)
            finally:
                gpxfile.close()
            subprocess.check_call(["gpsbabel", "-i", "gpx", "-o", "kml", gpxfilename, kmlfilename])
            subprocess.check_call(["zip", "-q", "-j", kmzfilename, kmlfilename])
            os.rename(kmzfilename, cachefilename)
        finally:
            for f in [gpxfilename, kmlfilename, kmzfilename]:
                if os.path.exists(f):
                    os.unlink(f)
            os.rmdir(tempdir)

    def render_short(self):
        title = "GPS"
        if self.annotation.title:
            title += ": %s" % self.annotation.title
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.url),
                                                               html.escape(title)))

    def render(self, request):
        self.ensure_cache_file()

        f = open(self.get_cache_filename(), "rb")
        try:
            content = f.read()
        finally:
            f.close()

        response = http.HttpResponse(content, content_type="application/vnd.google-earth.kmz")
        response["Content-Length"] = len(content)
        response['Content-Disposition'] = "attachment; filename=%s.kmz" % self.annotation.id

        return response

    def render_content_input(self, name, value, attrs=None):
        return forms.widgets.FileInput().render(name, value, attrs)

    def clean_content(self, content):
        return content and content.read() or None

    def after_save(self):
        cachefilename = self.get_cache_filename()
        if os.path.exists(cachefilename):
            os.unlink(cachefilename)

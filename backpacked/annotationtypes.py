from django.utils import html
from django.utils import safestring

from django import forms

from backpacked import models
from backpacked import utils

class UI(object):
    all = {}

    class Meta(type):
        def __init__(cls, name, bases, dct):
            if hasattr(cls, 'content_type'):
                UI.all[cls.content_type] = cls

    __metaclass__ = Meta

    title_required = True

    trip_allowed = True
    point_allowed = True
    segment_allowed = True

    def __init__(self, annotation):
        self.annotation = annotation

    def render_short(self):
        raise NotImplementedError()

    def render(self):
        raise NotImplementedError()

    def render_content_input(self, name, value, attrs=None):
        raise NotImplementedError()

    def clean_content(self, content):
        raise NotImplementedError()

class TextAnnotationUI(UI):
    content_type = models.ContentType.TEXT

    def render_short(self):
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.url),
                                                               html.escape(self.annotation.title)))

    def render(self):
        return self.annotation.content

    def render_content_input(self, name, value, attrs=None):
        return forms.widgets.Textarea().render(name, value, attrs)

    def clean_content(self, content):
        return content

class UrlAnnotationUI(UI):
    content_type = models.ContentType.URL

    def render_short(self):
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.content),
                                                               html.escape(self.annotation.title)))

    def render_content_input(self, name, value, attrs=None):
        return forms.widgets.TextInput().render(name, value, attrs)

    def clean_content(self, content):
        return forms.fields.URLField().clean(content)

class ExternalPhotosAnnotationUI(UrlAnnotationUI):
    content_type = models.ContentType.EXTERNAL_PHOTOS

Transportation = utils.Enum([(0, "Unspecified"),
                             (1, "Airplane"),
                             (2, "Bike"),
                             (3, "Boat"),
                             (4, "Bus"),
                             (5, "Car"),
                             (6, "Motorcycle"),
                             (7, "Train"),
                             (8, "Walk")])

class TransportationAnnotationUI(UI):
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

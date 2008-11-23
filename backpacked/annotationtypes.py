from django.utils import html
from django.utils import safestring

from django import forms

from backpacked import models

class TextAnnotationUI(models.Annotation.UI):
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

class UrlAnnotationUI(models.Annotation.UI):
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

import re

from django import forms
from django.utils import html
from django.utils import safestring

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

class ContentInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        return self.annotation.ui.render_content_input(name, value, attrs)

NoWidget = type("", (forms.widgets.Widget,), {'render': lambda *_, **__: ""})()

class AnnotationEditForm(forms.ModelForm):
    parent = forms.fields.ChoiceField()
    point = forms.fields.Field(widget=NoWidget, label="", required=False)
    segment = forms.fields.Field(widget=NoWidget, label="", required=False)
    content = forms.fields.CharField(widget=ContentInput())

    class Meta:
        model = models.Annotation
        fields = ('parent', 'point', 'segment', 'date', 'title', 'visibility', 'content')

    def __init__(self, data=None, files=None, instance=None):
        super(AnnotationEditForm, self).__init__(data, files, instance=instance)

        points = list(instance.trip.point_set.all())
        segments = sorted(list(instance.trip.segment_set.all()))
        self.fields['parent'].choices = [("p_%s" % p.id, p.name) for p in points] + \
                                        [("s_%s" % s.id, unicode(s)) for s in segments]

        if instance.point_id:
            self.initial['parent'] = "p_%s" % instance.point_id
        elif instance.segment_id:
            self.initial['parent'] = "s_%s" % instance.segment_id
        else:
            self.initial['parent'] = ""

        self.fields['content'].widget.annotation = instance

    def clean_content(self):
        return self.instance.ui.clean_content(self.cleaned_data['content'])

    def clean(self):
        parent = self.cleaned_data['parent']
        assert re.match(r"^[ps]_\d+$", parent)
        id = int(parent[2:])
        self.cleaned_data['point'] = self.cleaned_data['segment'] = None
        if parent.startswith("p_"):
            self.cleaned_data['point'] = models.Point.objects.get(id=id)
        elif parent.startswith("s_"):
            self.cleaned_data['segment'] = models.Segment.objects.get(id=id)

        return self.cleaned_data

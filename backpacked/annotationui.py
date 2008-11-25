import re

from django import forms

from backpacked import models

import settings

class ContentInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        return self.annotation.manager.render_content_input(name, value, attrs)

class ParentField(forms.fields.ChoiceField):
    def _get_annotation(self):
        return self._annotation

    def _set_annotation(self, annotation):
        self._annotation = annotation
        points = sorted(list(annotation.trip.point_set.all()))
        choices = []
        if annotation.manager.trip_allowed:
            choices += [("", "")]
        if annotation.manager.point_allowed:
            choices += [("p_%s" % p.id, p.name) for p in points]
        if annotation.manager.segment_allowed:
            for i in range(len(points) - 1):
                choices.append(("s_%s" % points[i].id, "%s - %s" % (points[i].name, points[i + 1].name)))
        self.choices = choices

    annotation = property(_get_annotation, _set_annotation)

class NoWidget(forms.widgets.Widget):
    def render(*_, **__):
        return ""

parent_re = re.compile(r"^[ps]_\d+$")

class PointInput(NoWidget):
    def value_from_datadict(self, data, *_):
        parent = data.get('parent')
        if not parent:
            return None
        else:
            assert parent_re.match(parent)
            return models.Point.objects.get(id=int(parent[2:]))

class SegmentInput(NoWidget):
    def value_from_datadict(self, data, *_):
        parent = data.get('parent')
        if not parent:
            return False
        else:
            assert parent_re.match(parent)
            return parent[0] == "s"

class AnnotationEditForm(forms.ModelForm):
    title = forms.fields.CharField(max_length=30)
    date = forms.fields.DateField(widget=forms.widgets.DateTimeInput(format=settings.DATE_FORMAT_SHORT_PY), required=False)
    parent = ParentField()
    visibility = forms.fields.ChoiceField(choices=models.Visibility.choices)
    content = forms.fields.CharField(widget=ContentInput())
    point = forms.fields.Field(widget=PointInput(), label="")
    segment = forms.fields.Field(widget=SegmentInput(), label="")

    class Meta:
        fields = ('title', 'date', 'parent', 'visibility', 'content') + \
                 ('point', 'segment') # editable through the 'parent' field

    def __init__(self, data=None, files=None, annotation=None):
        super(AnnotationEditForm, self).__init__(data, files, instance=annotation)

        if annotation.point_id:
            self.initial['parent'] = "%s_%s" % (annotation.segment and "s" or "p", annotation.point_id)
        else:
            self.initial['parent'] = ""

        self.fields['parent'].annotation = annotation

        self.fields['content'].widget.annotation = annotation
        self.fields['content'].label = annotation.content_type_h
        if annotation.manager.has_extended_content:
            try:
                self.initial['content'] = annotation.extended_content.content
            except models.ExtendedAnnotationContent.DoesNotExist:
                pass

        if hasattr(annotation.manager, 'exclude_fields'):
            for f in annotation.manager.exclude_fields:
                self.fields[f].label = ""
                self.fields[f].widget = NoWidget()
        self.fields['title'].required = annotation.manager.title_required

    def clean_content(self):
        return self.instance.manager.clean_content(self.cleaned_data['content'])

    def save(self):
        instance = super(AnnotationEditForm, self).save()

        if not self.instance.manager.has_extended_content:
            return instance

        content = self.cleaned_data.pop('content')
        try:
            extended_content = models.ExtendedAnnotationContent.objects.get(annotation=instance)
        except models.ExtendedAnnotationContent.DoesNotExist:
            extended_content = models.ExtendedAnnotationContent(annotation_id=instance.id)
        extended_content.content = content
        extended_content.save()

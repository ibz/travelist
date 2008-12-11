import re

from django import forms

from backpacked import models
from backpacked import ui

import settings

class ContentInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        return self.annotation.manager.render_content_input(name, value, final_attrs)

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
    is_hidden = True

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

class EditForm(ui.ModelForm):
    title = forms.fields.CharField(max_length=30, widget=forms.widgets.TextInput(attrs={'class': 'title'}))
    date = forms.fields.DateField(widget=forms.widgets.DateTimeInput(format=settings.DATE_FORMAT_SHORT_PY, attrs={'class': 'text'}), required=False)
    parent = ParentField()
    visibility = forms.fields.ChoiceField(choices=models.Visibility.choices)
    content = forms.fields.CharField(widget=ContentInput(attrs={'class': 'text'}))
    point = forms.fields.Field(widget=PointInput(), label="")
    segment = forms.fields.Field(widget=SegmentInput(), label="")

    class Meta:
        fields = ('title', 'date', 'parent', 'visibility', 'content') + \
                 ('point', 'segment') # editable through the 'parent' field

    def __init__(self, data=None, files=None, annotation=None, initial=None, edit_parent=True):
        super(EditForm, self).__init__(data, files, initial=initial, instance=annotation)

        if edit_parent:
            if not 'parent' in self.initial:
                if annotation.point_id:
                    self.initial['parent'] = "%s_%s" % (annotation.segment and "s" or "p", annotation.point_id)
                else:
                    self.initial['parent'] = ""
            self.fields['parent'].annotation = annotation
        else:
            self.fields['parent'].widget = forms.widgets.HiddenInput()

        if annotation.manager.edit_content_as_file:
            self.fields['content'] = forms.fields.FileField(widget=ContentInput(), required=False)

        self.fields['content'].widget.annotation = annotation
        self.fields['content'].label = annotation.content_type_h
        if not annotation.manager.edit_content_as_file:
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
        if self.instance.manager.edit_content_as_file:
            return self.instance.manager.clean_content(self.files.get('content'))
        else:
            return self.instance.manager.clean_content(self.cleaned_data['content'])

    def save(self):
        if not self.instance.manager.has_extended_content:
            return super(EditForm, self).save()

        content = self.cleaned_data.pop('content')
        instance = super(EditForm, self).save()
        try:
            extended_content = models.ExtendedAnnotationContent.objects.get(annotation=instance)
        except models.ExtendedAnnotationContent.DoesNotExist:
            extended_content = models.ExtendedAnnotationContent(annotation_id=instance.id)
        if content is not None:
            extended_content.content = content
        extended_content.save()

import re

from django import forms

from backpacked import models
from backpacked import ui

import settings

class NoWidget(forms.widgets.Widget):
    is_hidden = True

    def render(*_, **__):
        return ""

class EditForm(ui.ModelForm):
    title = forms.fields.CharField(max_length=30, widget=forms.widgets.TextInput(attrs={'class': 'title'}))
    visibility = forms.fields.ChoiceField(choices=models.Visibility.choices)
    point = forms.models.ModelChoiceField(models.Point.objects, required=False, widget=forms.widgets.HiddenInput(), label="")
    segment = forms.fields.BooleanField(required=False, widget=forms.widgets.HiddenInput(), label="")
    content = forms.fields.Field()

    class Meta:
        fields = ('title', 'visibility', 'point', 'segment', 'content')

    def __init__(self, data=None, files=None, annotation=None, initial=None):
        super(EditForm, self).__init__(data, files, initial=initial, instance=annotation)

        if annotation.manager.edit_content_as_file:
            self.fields['content'] = forms.fields.FileField(required=False)

        self.fields['content'].widget = annotation.manager.widget()
        self.fields['content'].widget.annotation = annotation
        if annotation.manager.show_content_label:
            self.fields['content'].label = annotation.content_type_h
        else:
            self.fields['content'].label = ""
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
            return self.instance.manager.clean_content(self.cleaned_data.get('content'))

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

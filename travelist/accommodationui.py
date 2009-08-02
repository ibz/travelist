from django import forms

from travelist import models
from travelist import ui

class EditForm(ui.ModelForm):
    wiki_content = forms.fields.CharField(widget=forms.widgets.Textarea(attrs={'class': 'text', 'style': "height: 300px; width: 500px"}), required=False)
    class Meta:
        model = models.Accommodation
        fields = ('wiki_content',)

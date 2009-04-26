from django import forms

from backpacked import models
from backpacked import ui

class EditForm(ui.ModelForm):
    wiki_content = forms.fields.CharField(widget=forms.widgets.Textarea(attrs={'class': 'text', 'style': "height: 300px; width: 500px"}))
    class Meta:
        model = models.Accommodation
        fields = ('wiki_content',)

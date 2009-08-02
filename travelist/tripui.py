from django import forms

from travelist import models
from travelist import ui

class EditForm(ui.ModelForm):
    name = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={'class': 'title'}))
    start_date = forms.fields.DateField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    end_date = forms.fields.DateField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    class Meta:
        model = models.Trip
        fields = ('name', 'start_date', 'end_date', 'visibility')

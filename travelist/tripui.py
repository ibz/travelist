from django import forms

from travelist import models
from travelist import ui

class EditForm(ui.ModelForm):
    name = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={'class': 'title'}))
    start_date = forms.fields.DateField(widget=forms.widgets.TextInput(attrs={'class': 'text'}), error_messages={'invalid': "Please enter the date as yyyy-mm-dd."})
    end_date = forms.fields.DateField(widget=forms.widgets.TextInput(attrs={'class': 'text'}), error_messages={'invalid': "Please enter the date as yyyy-mm-dd."})
    class Meta:
        model = models.Trip
        fields = ('name', 'start_date', 'end_date', 'visibility')

from django import forms

from backpacked import models

class TripEditForm(forms.ModelForm):
    class Meta:
        model = models.Trip
        fields = ('name', 'start_date', 'end_date', 'visibility')

from django import newforms as forms
from django.core import validators
from django.contrib.auth.models import User

from web.models import Location
from web.models import UserProfile

class LocationInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if value:
            loc_id, loc_name = value.id, value.name
        else:
            loc_id, loc_name = "", ""
        return (
"""<input type=\"text\" value="%(loc_name)s" onkeydown="javascript:autoCompleteLocation('id_%(name)s');"%(attrs)s />
<input type="hidden" value="%(loc_id)s" name="%(name)s"%(attrs)s />"""
            % {'loc_name': loc_name,
               'loc_id': loc_id,
               'name': name,
               'attrs': forms.util.flatatt(attrs)})

class LocationChoiceField(forms.fields.Field):
    widget=LocationInput

    def clean(self, value):
        super(LocationChoiceField, self).clean(value)

class AccountDetailsForm(forms.ModelForm):
    name = forms.CharField()
    current_location = LocationChoiceField()
    about = forms.CharField(widget=forms.widgets.Textarea)

    class Meta:
        model = UserProfile
        fields = ('name', 'current_location', 'about')

class AccountRegistrationForm(forms.ModelForm):
    username = forms.CharField(help_text="Use letters, digits and underscores for this.")
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise validators.ValidationError("The username \"%s\" is already taken." % username)

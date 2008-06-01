from django import newforms as forms
from django.newforms import fields
from django.core import validators
from django.contrib.auth.models import User
from django.newforms.util import ValidationError

from web.models import Location
from web.models import Trip
from web.models import UserProfile

class LocationInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if value:
            loc = Location.objects.get(id=value)
            loc_id, loc_name = loc.id, loc.name
        else:
            loc_id, loc_name = "", ""
        return (
"""<input type=\"text\" value="%(loc_name)s" id="id_%(name)s_name" />
<input type="hidden" value="%(loc_id)s" name="%(name)s"%(attrs)s />
<script type="text/javascript">
$("#id_%(name)s_name").autocomplete("/location/",
    {minChars: 2,
     onItemSelect: function(li) { $("#id_%(name)s").attr('value', li.extra[0]); }});
</script>
"""
            % {'loc_name': loc_name,
               'loc_id': loc_id,
               'name': name,
               'attrs': forms.util.flatatt(attrs)})

class LocationChoiceField(forms.fields.ChoiceField):
    def __init__(self, required=True, widget=LocationInput, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        fields.Field.__init__(self, required, widget, label, initial, help_text,
                       *args, **kwargs)

    def clean(self, value):
        fields.Field.clean(self, value)
        if value in fields.EMPTY_VALUES:
            return None
        try:
            return Location.objects.get(pk=value)
        except Location.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'])

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

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ('name', 'start_date', 'end_date')

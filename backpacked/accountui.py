import re

from django import forms

from backpacked import models
from backpacked import placeui

class AccountLoginForm(forms.Form):
    username = forms.fields.CharField()
    password = forms.fields.CharField(widget=forms.widgets.PasswordInput)

class AccountDetailsForm(forms.ModelForm):
    name = forms.fields.CharField(required=False)
    current_location = placeui.PlaceChoiceField(required=False)
    about = forms.fields.CharField(widget=forms.widgets.Textarea(), required=False)

    class Meta:
        model = models.UserProfile
        fields = ('name', 'current_location', 'about')

class AccountRegistrationForm(forms.ModelForm):
    USERNAME_RE = re.compile(r"^\w+$")
    USERNAME_BLACKLIST = ["admin", "root"] + \
                         ["media", "account", "trip", "place", "annotation", "segment", "point"] + \
                         ["faq", "friend", "contact", "feed", "settings", "help", "profile", "explore"]

    username = forms.fields.CharField()
    email = forms.fields.EmailField()
    password = forms.fields.CharField(widget=forms.widgets.PasswordInput)
    alpha_code = forms.fields.CharField()

    class Meta:
        model = models.User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username']
        if not self.USERNAME_RE.match(username):
            raise forms.util.ValidationError("The username should contain only letters, digits and underscores.")
        if username in self.USERNAME_BLACKLIST:
            raise forms.util.ValidationError("That username is not available.")
        try:
            models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            return username
        raise forms.util.ValidationError("That username is not available.")

    def clean_alpha_code(self):
        if self.cleaned_data['alpha_code'] != "i want the alpha!":
            raise forms.util.ValidationError("The alpha code is invalid.")

    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

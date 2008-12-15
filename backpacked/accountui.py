import re

from django import forms
from django.contrib import auth

from backpacked import models
from backpacked import placeui
from backpacked import ui

class LoginForm(ui.Form):
    username = forms.fields.CharField(required=False, widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    password = forms.fields.CharField(required=False, widget=forms.widgets.PasswordInput(attrs={'class': 'text'}))

    def clean(self):
        user = auth.authenticate(username=self.cleaned_data.get('username'),
                                 password=self.cleaned_data.get('password'))
        if not user:
            raise forms.util.ValidationError("The username or password is invalid.")
        if not user.is_active:
            raise forms.util.ValidationError("The user account has been disabled.")
        self.cleaned_data['user'] = user
        return self.cleaned_data

class ProfileForm(ui.ModelForm):
    name = forms.fields.CharField(required=False, widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    current_location = placeui.PlaceChoiceField(required=False)
    about = forms.fields.CharField(required=False, widget=forms.widgets.Textarea(attrs={'class': 'text'}))

    class Meta:
        model = models.UserProfile
        fields = ('name', 'current_location', 'about', 'picture')

class RegistrationForm(ui.ModelForm):
    USERNAME_RE = re.compile(r"^[^\d]\w*$")
    USERNAME_BLACKLIST = ["admin", "root"] + \
                         ["media", "account", "trip", "place", "annotation", "segment", "point"] + \
                         ["faq", "friend", "contact", "feed", "settings", "help", "profile", "explore"]

    username = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    email = forms.fields.EmailField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    password = forms.fields.CharField(widget=forms.widgets.PasswordInput(attrs={'class': 'text'}))
    alpha_code = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))

    class Meta:
        model = models.User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username']
        if not self.USERNAME_RE.match(username):
            raise forms.util.ValidationError("The username should contain only letters, digits and underscores and cannot start with a digit.")
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

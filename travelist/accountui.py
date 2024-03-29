import re

from PIL import Image

from django import forms
from django.contrib import auth

from travelist import models
from travelist import placeui
from travelist import ui

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
    PICTURE_MAX_SIZE = (125, 125) # NB: Don't forget to edit CSS when changing this!

    name = forms.fields.CharField(required=False, widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    current_location = placeui.PlaceChoiceField(required=False)
    about = forms.fields.CharField(required=False, widget=forms.widgets.Textarea(attrs={'class': 'text'}))

    class Meta:
        model = models.UserProfile
        fields = ('name', 'current_location', 'about', 'picture')

    def save(self):
        profile = super(ProfileForm, self).save()
        if self.cleaned_data.get('picture'):
            image = Image.open(profile.picture.path)
            image.thumbnail(self.PICTURE_MAX_SIZE, Image.ANTIALIAS)
            image.save(profile.picture_thumbnail_path, quality=85, optimize=True)
        return profile

class ProfileConnectForm(forms.Form):
    scan_existing_tweets = forms.CharField(widget=forms.widgets.HiddenInput(), required=False)
    twitter_username = forms.CharField(max_length=40, widget=forms.widgets.TextInput(attrs={'class': 'text'}),
                                       required=False,
                                       help_text="<a href=\"/help/twitter/\" target=\"_blank\" title=\"What's this?\">?</a>")
    flickr_userid = forms.CharField(max_length=40, widget=forms.widgets.TextInput(attrs={'class': 'text'}),
                                       required=False,
                                       help_text="<a href=\"/help/flickr/\" target=\"_blank\" title=\"What's this?\">?</a>")

class RegistrationForm(ui.ModelForm):
    USERNAME_RE = re.compile(r"^[^\d]\w*$")
    USERNAME_BLACKLIST = ["admin", "root"] + \
                         ["media", "account", "trip", "place", "annotation", "segment", "point"] + \
                         ["faq", "friend", "contact", "feed", "settings", "help", "profile", "explore"]

    username = forms.fields.CharField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    email = forms.fields.EmailField(widget=forms.widgets.TextInput(attrs={'class': 'text'}))
    password = forms.fields.CharField(widget=forms.widgets.PasswordInput(attrs={'class': 'text'}))

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

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

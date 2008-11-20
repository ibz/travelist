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
    username = forms.fields.CharField(help_text="Use letters, digits and underscores for this.")
    email = forms.fields.EmailField()
    password = forms.fields.CharField(widget=forms.widgets.PasswordInput)
    alpha_code = forms.fields.CharField()

    class Meta:
        model = models.User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            return username
        raise forms.util.ValidationError("The username \"%s\" is already taken." % username)

    def clean_alpha_code(self):
        if self.cleaned_data['alpha_code'] != "i want the alpha!":
            raise forms.util.ValidationError("The alpha code is invalid.")

    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

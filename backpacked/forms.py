import re

from django import forms
from django.forms import fields
from django.forms import widgets
from django.contrib.auth.models import User
from django.forms.util import ValidationError
from django.utils import html
from django.utils import safestring

from backpacked import models
from backpacked.models import Annotation
from backpacked.models import Place
from backpacked.models import Point
from backpacked.models import Segment
from backpacked.models import Trip
from backpacked.models import UserProfile
from backpacked.utils import find

class PlaceInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if value:
            loc = Place.objects.get(id=value)
            loc_id, loc_name = loc.id, loc.name
        else:
            loc_id, loc_name = "", ""
        return (
"""<input type="text" value="%(loc_name)s" id="id_%(name)s_name" />
<input type="hidden" value="%(loc_id)s" name="%(name)s"%(attrs)s />
<script type="text/javascript">
$("#id_%(name)s_name").autocomplete("/place/search/",
    {minChars: 2, matchSubset: false,
     onItemSelect: function(li) { $("#id_%(name)s").attr('value', li.extra[0]); }});
</script>
"""
            % {'loc_name': loc_name,
               'loc_id': loc_id,
               'name': name,
               'attrs': attrs and forms.util.flatatt(attrs) or ""})

class PlaceChoiceField(fields.ChoiceField):
    def __init__(self, required=True, widget=PlaceInput, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        fields.Field.__init__(self, required, widget, label, initial, help_text, *args, **kwargs)

    def clean(self, value):
        fields.Field.clean(self, value)
        if value in fields.EMPTY_VALUES:
            return None
        try:
            return Place.objects.get(pk=value)
        except Place.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'])

class AccountLoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class AccountDetailsForm(forms.ModelForm):
    name = forms.CharField(required=False)
    current_location = PlaceChoiceField(required=False)
    about = forms.CharField(widget=forms.widgets.Textarea, required=False)

    class Meta:
        model = UserProfile
        fields = ('name', 'current_location', 'about')

class AccountRegistrationForm(forms.ModelForm):
    username = forms.CharField(help_text="Use letters, digits and underscores for this.")
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    alpha_code = forms.CharField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise ValidationError("The username \"%s\" is already taken." % username)

    def clean_alpha_code(self):
        if self.cleaned_data['alpha_code'] != "i want the alpha!":
            raise ValidationError("The alpha code is invalid.")

    def save(self, commit=True):
        user = super(forms.ModelForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class TripEditForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ('name', 'start_date', 'end_date', 'visibility')

class TextAnnotationUI(models.Annotation.UI):
    content_type = models.ContentType.TEXT

    def render_short(self):
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.url),
                                                               html.escape(self.annotation.title)))

    def render(self):
        return self.annotation.content

    def render_content_input(self, name, value, attrs=None):
        return widgets.Textarea().render(name, value, attrs)

    def clean_content(self, content):
        return content

class UrlAnnotationUI(models.Annotation.UI):
    content_type = models.ContentType.URL

    def render_short(self):
        return safestring.mark_safe("<a href=\"%s\">%s</a>" % (html.escape(self.annotation.content),
                                                               html.escape(self.annotation.title)))

    def render_content_input(self, name, value, attrs=None):
        return widgets.TextInput().render(name, value, attrs)

    def clean_content(self, content):
        return fields.URLField().clean(content)

class ExternalPhotosAnnotationUI(UrlAnnotationUI):
    content_type = models.ContentType.EXTERNAL_PHOTOS

class ContentInput(widgets.Widget):
    def render(self, name, value, attrs=None):
        return self.annotation.ui.render_content_input(name, value, attrs)

NoWidget = type("", (widgets.Widget,), {'render': lambda *_, **__: ""})()

class AnnotationEditForm(forms.ModelForm):
    parent = fields.ChoiceField()
    point = fields.Field(widget=NoWidget, label="", required=False)
    segment = fields.Field(widget=NoWidget, label="", required=False)
    content = fields.CharField(widget=ContentInput())

    class Meta:
        model = Annotation
        fields = ('parent', 'point', 'segment', 'date', 'title', 'visibility', 'content')

    def __init__(self, data=None, files=None, instance=None):
        super(AnnotationEditForm, self).__init__(data, files, instance=instance)

        points = list(instance.trip.point_set.all())
        segments = sorted(list(instance.trip.segment_set.all()))
        self.fields['parent'].choices = [("p_%s" % p.id, p.name) for p in points] + \
                                        [("s_%s" % s.id, unicode(s)) for s in segments]

        if instance.point_id:
            self.initial['parent'] = "p_%s" % instance.point_id
        elif instance.segment_id:
            self.initial['parent'] = "s_%s" % instance.segment_id
        else:
            self.initial['parent'] = ""

        self.fields['content'].widget.annotation = instance

    def clean_content(self):
        return self.instance.ui.clean_content(self.cleaned_data['content'])

    def clean(self):
        parent = self.cleaned_data['parent']
        assert re.match(r"^[ps]_\d+$", parent)
        id = int(parent[2:])
        self.cleaned_data['point'] = self.cleaned_data['segment'] = None
        if parent.startswith("p_"):
            self.cleaned_data['point'] = models.Point.objects.get(id=id)
        elif parent.startswith("s_"):
            self.cleaned_data['segment'] = models.Segment.objects.get(id=id)

        return self.cleaned_data

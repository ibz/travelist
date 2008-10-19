import re

from django import forms
from django.forms import fields
from django.forms import widgets
from django.contrib.auth.models import User
from django.forms.util import ValidationError

from backpacked import models
from backpacked.models import Annotation
from backpacked.models import Place
from backpacked.models import Point
from backpacked.models import Segment
from backpacked.models import Trip
from backpacked.models import UserProfile
from backpacked.models import TRANSPORTATION_METHODS
from backpacked.utils import group_items
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

class ContentInput(widgets.Widget):
    def __init__(self, content_type, content_type_selector, top_level=False,
                 attrs=None):
        super(ContentInput, self).__init__(attrs)
        self.content_type = content_type
        self.content_type_selector = content_type_selector
        self.top_level = top_level

    def render(self, name, value, attrs=None):
        if self.content_type == models.TEXT:
            widget = widgets.Textarea()
        elif self.content_type == models.URL:
            widget = widgets.TextInput()
        else:
            widget = None

        widget = widget and widget.render(name, value, attrs) or ""

        if not self.top_level:
            return widget

        return ("<div id=\"%(name)s\">%(widget)s</div>"
                "<script type=\"text/javascript\">"
                "registerContentTypeEvent('%(selector)s', '%(name)s');"
                "</script>"
                % {'name': name,
                   'widget': widget,
                   'selector': self.content_type_selector})

class SegmentInput(widgets.Widget):
    def render(self, name, value, attrs=None):
        place = PlaceInput()
        date = widgets.DateTimeInput()
        transportation = widgets.Select(choices=TRANSPORTATION_METHODS)
        return ("%s|%s|%s|%s|%s"
                % (place.render("%s_p1_place" % name,
                                value and value.p1_id and value.p1.place_id,
                                {'id': "id_%s_p1_place" % name}),
                   date.render("%s_start_date" % name,
                               value and value.start_date),
                   place.render("%s_p2_place" % name,
                                value and value.p2_id and value.p2.place_id,
                                {'id': "id_%s_p2_place" % name}),
                   date.render("%s_end_date" % name,
                               value and value.end_date),
                   transportation.render("%s_transportation_method" % name,
                                         value and value.transportation_method)))

    def value_from_datadict(self, data, files, name):
        segment = {}
        for member in ['p1_place', 'p2_place', 'start_date', 'end_date', 'transportation_method']:
            segment[member] = data["%s_%s" % (name, member)]
        return segment

class PathInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        segment_input = SegmentInput()
        render_segment = lambda i: segment_input.render("%s_%s" % (name, i), value[i], attrs).replace("|", "</td><td>")
        if value == []:
            value = [Segment()]
        segments = "".join(["<tr><td>%s</td></tr>" % render_segment(i)
                            for i in range(len(value))])
        return (
"""
<table id="path_%(name)s">
<thead>
    <td>From</td>
    <td>Start date</td>
    <td>To</td>
    <td>End date</td>
    <td>Transportation method</td>
</thead>
<tbody>%(items)s</tbody>
</table>
<a class="navigation" href="javascript:newSegment();">Add segment</a>
<script type="text/javascript">
function newSegment()
{
    var index = document.getElementById("path_%(name)s").getElementsByTagName("tbody")[0].childNodes.length;
    addTableRow("path_%(name)s",
                "/widget/segment_input/?name=%(name)s_" + index);
}
</script>
"""
            % {'name': name,
               'items': segments})

    def value_from_datadict(self, data, files, name):
        input_re = re.compile(
            # inputs look like path_0_p1_place, path_0_start_date, ...
            r"^%s_(?P<i>\d+)_(p[12]_place|(start|end)_date|transportation_method)$" % name)
        indices = [int(m.group('i'))
                   for m in [input_re.match(k)
                             for k in data.keys()]
                   if m]
        segment_input = SegmentInput()
        return [segment_input.value_from_datadict(data, files, "%s_%s" % (name, i))
                for i in set(indices)]

class PathField(fields.Field):
    def __init__(self, widget=PathInput, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        fields.Field.__init__(self, False, widget, label, initial, help_text, *args, **kwargs)

    def clean(self, value):
        datetime_field = fields.DateTimeField(required=False)
        choice_field = fields.ChoiceField(choices=TRANSPORTATION_METHODS, required=False)
        segments, places = [], []
        for segment_data in value:
            if segment_data['p1_place'] is None or segment_data['p2_place'] is None:
                continue
            segment = {'p1_place': int(segment_data['p1_place']),
                       'p2_place': int(segment_data['p2_place']),
                       'start_date': datetime_field.clean(segment_data['start_date']),
                       'end_date': datetime_field.clean(segment_data['end_date']),
                       'transportation_method':
                           int(choice_field.clean(segment_data['transportation_method']))}
            segments.append(segment)
            for l in [segment['p1_place'], segment['p2_place']]:
                if not l in places:
                    places.append(l)
        return segments, places

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

class AnnotationNewForm(forms.ModelForm):
    content = fields.CharField(widget=ContentInput(None, 'content_type', True))

    class Meta:
        model = Annotation
        fields = ('date', 'title', 'visibility', 'content_type', 'content')

    def clean_content(self):
        content_type = self.cleaned_data.has_key('content_type') \
            and int(self.cleaned_data['content_type']) \
            or self.instance.content_type
        if content_type == models.TEXT:
            return self.cleaned_data['content']
        elif content_type == models.URL:
            return fields.URLField().clean(self.cleaned_data['content'])

class AnnotationEditForm(AnnotationNewForm):
    def __init__(self, data=None, files=None, instance=None):
        super(AnnotationEditForm, self).__init__(data, files,
                                                 instance=instance)
        self.fields['content'].widget.content_type = instance.content_type

    class Meta:
        model = Annotation
        fields = tuple([f for f in AnnotationNewForm.Meta.fields
                        if f != 'content_type'])

import re

from django import newforms as forms
from django.newforms import fields
from django.newforms import widgets
from django.core import validators
from django.contrib.auth.models import User
from django.newforms.util import ValidationError

from web.models import Location
from web.models import Point
from web.models import Segment
from web.models import Trip
from web.models import UserProfile
from web.models import TRANSPORTATION_METHODS

class LocationInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        if value:
            loc = Location.objects.get(id=value)
            loc_id, loc_name = loc.id, loc.name
        else:
            loc_id, loc_name = "", ""
        return (
"""<input type="text" value="%(loc_name)s" id="id_%(name)s_name" />
<input type="hidden" value="%(loc_id)s" name="%(name)s"%(attrs)s />
<script type="text/javascript">
$("#id_%(name)s_name").autocomplete("/location/search/",
    {minChars: 2,
     onItemSelect: function(li) { $("#id_%(name)s").attr('value', li.extra[0]); }});
</script>
"""
            % {'loc_name': loc_name,
               'loc_id': loc_id,
               'name': name,
               'attrs': attrs and forms.util.flatatt(attrs) or ""})

class LocationChoiceField(fields.ChoiceField):
    def __init__(self, required=True, widget=LocationInput, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        fields.Field.__init__(self, required, widget, label, initial, help_text, *args, **kwargs)

    def clean(self, value):
        fields.Field.clean(self, value)
        if value in fields.EMPTY_VALUES:
            return None 
        try:
            return Location.objects.get(pk=value)
        except Location.DoesNotExist:
            raise ValidationError(self.error_messages['invalid_choice'])

class SegmentInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        location = LocationInput()
        date = widgets.DateTimeInput()
        transportation = widgets.Select(choices=TRANSPORTATION_METHODS)
        return (location.render("%s_p1_location" % name, None,
                                   {'id': "id_%s_p1_location" % name})
              + date.render("%s_start_date" % name, None)
              + location.render("%s_p2_location" % name, None,
                                   {'id': "id_%s_p2_location" % name})
              + date.render("%s_end_date" % name, None)
              + transportation.render("%s_transportation_method" % name, None))

    def value_from_datadict(self, data, files, name):
        segment = {}
        for member in ['p1_location', 'p2_location', 'start_date', 'end_date', 'transportation_method']:
            segment[member] = data["%s_%s" % (name, member)]
        return segment

class PathInput(forms.widgets.Widget):
    def render(self, name, value, attrs=None):
        return (
"""
<li id="path_%(name)s">%(items)s</li>
<a href="javascript:newSegment();">More</a>
<script type="text/javascript">
function newSegment()
{
    var index = document.getElementById("path_%(name)s").childNodes.length;
    addListItem("path_%(name)s",
                "/widget/segment_input/?name=%(name)s_" + index);
}
</script>
"""
            % {'name': name,
               'items': ""})

    def value_from_datadict(self, data, files, name):
        input_re = re.compile(
            # inputs look like path_0_p1_location, path_0_start_date, ...
            r"^%s_(?P<i>\d+)_(p[12]_location|(start|end)_date|transportation_method)$" % name)
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

    def _get_point(self, points, location_id):
        for point in points:
            if point.location_id == location_id:
                return point
        point = Point(location_id=location_id)
        points.append(point)
        return point

    def clean(self, value):
        datetime_field = fields.DateTimeField(required=False)
        choice_field = fields.ChoiceField(choices=TRANSPORTATION_METHODS, required=False)
        segments, points = [], []
        for data in value:
            segment = Segment()
            p1_location = int(data['p1_location'])
            p2_location = int(data['p2_location'])
            start_date = datetime_field.clean(data['start_date'])
            end_date = datetime_field.clean(data['end_date'])
            transportation_method = choice_field.clean(data['transportation_method'])
            segment.p1 = self._get_point(points, p1_location)
            segment.p2 = self._get_point(points, p2_location)
            segment.start_date = start_date
            segment.end_date = end_date
            segment.transportation_method = transportation_method
            segments.append(segment)
        return segments, points

class AccountDetailsForm(forms.ModelForm):
    name = forms.CharField(required=False)
    current_location = LocationChoiceField(required=False)
    about = forms.CharField(widget=forms.widgets.Textarea, required=False)

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

class TripEditForm(forms.ModelForm):
    path = PathField()

    class Meta:
        model = Trip
        fields = ('name', 'start_date', 'end_date', 'path')

    def save(self, commit=True):
        trip = super(TripEditForm, self).save(False)
        segments, points = trip.segments, trip.points
        new_segments, new_points = self.cleaned_data['path']
        
        return trip

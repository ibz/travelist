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
from web.utils import group_items
from web.utils import find

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

class SegmentInput(widgets.Widget):
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

    def clean(self, value):
        datetime_field = fields.DateTimeField(required=False)
        choice_field = fields.ChoiceField(choices=TRANSPORTATION_METHODS, required=False)
        segments, locations = [], []
        for segment_data in value:
            segment = {'p1_location': int(segment_data['p1_location']),
                       'p2_location': int(segment_data['p2_location']),
                       'start_date': datetime_field.clean(segment_data['start_date']),
                       'end_date': datetime_field.clean(segment_data['end_date']),
                       'transportation_method':
                           int(choice_field.clean(segment_data['transportation_method']))}
            segments.append(segment)
            for l in [segment['p1_location'], segment['p2_location']]:
                if not l in locations:
                    locations.append(l)
        return segments, locations

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

    def _get_locations(self, segment_data):
        return (segment_data['p1_location'], segment_data['p2_location'])

    def _create_point(self, trip, location_id):
        location = Location.objects.get(id=location_id)
        point = Point(trip=trip, location=location)
        point.name=location.name
        point.coords=location.coords
        point.save()

    def _create_segment(self, trip, data):
        segment = Segment(trip=trip)
        segment.p1 = Point.objects.get(trip=trip, location__id=data['p1_location'])
        segment.p2 = Point.objects.get(trip=trip, location__id=data['p2_location'])
        segment.start_date=data['start_date']
        segment.end_date=data['end_date']
        segment.transportation_method = data['transportation_method']
        segment.save()

    def save(self):
        trip = super(TripEditForm, self).save()

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())
        new_segments_data, new_points_data = self.cleaned_data['path']

        # delete points
        for point in points:
            if point.location_id not in new_points_data:
                # TODO: check for annotations
                point.delete()

        # add points
        for new_point_data in new_points_data:
            if not find(points, lambda p: p.location_id == new_point_data):
                self._create_point(trip, new_point_data)

        # delete segments
        for segment in segments:
            if not find(new_segments_data,
                        lambda s: segment.locations_equal(self._get_locations(s))):
                # TODO: check for annotations
                segment.delete()

        # add / edit segments
        segments_grouped = group_items(segments, Segment.locations_equal)
        new_segments_data_grouped = \
            group_items(new_segments_data,
                        lambda a, b: self._get_locations(a) == self._get_locations(b))

        for new_group in new_segments_data_grouped:
            match = lambda g: g[0].locations_equal(self._get_locations(new_group[0]))
            existing_group = find(segments_grouped, match)

            if existing_group:
                new_group.sort(lambda a, b: cmp(a['start_date'], b['start_date']))
                existing_group.sort()

                # delete segments
                for segment in existing_group[len(new_group):]:
                    # TODO: check annotations
                    segment.delete()

                # modify segments
                for i in range(min(len(new_group), len(existing_group))):
                    existing_group[i].start_date = new_group[i]['start_date']
                    existing_group[i].end_date = new_group[i]['end_date']
                    existing_group[i].transportation_method = new_group[i]['transportation_method']
                    existing_group[i].save()

                # add segments
                for data in new_group[len(existing_group):]:
                    self._create_segment(trip, data)
            else: # add all segments in this group
                for data in new_group:
                    self._create_segment(trip, data)
        return trip

import re

from django import newforms as forms
from django.newforms import fields
from django.newforms import widgets
from django.core import validators
from django.contrib.auth.models import User
from django.newforms.util import ValidationError

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
    {minChars: 2,
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
    var index = document.getElementById("path_%(name)s").childNodes.length;
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
        fields = ('name', 'start_date', 'end_date', 'visibility', 'path')

    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self._populate_path()

    def _populate_path(self):
        segments = list(self.instance.segment_set.all())
        segments.sort()
        self.initial['path'] = segments

    def _get_places(self, segment_data):
        return (segment_data['p1_place'], segment_data['p2_place'])

    def _create_point(self, trip, place_id):
        place = Place.objects.get(id=place_id)
        point = Point(trip=trip, place=place)
        point.name=place.name
        point.coords=place.coords
        point.save()

    def _create_segment(self, trip, data):
        segment = Segment(trip=trip)
        segment.p1 = Point.objects.get(trip=trip, place__id=data['p1_place'])
        segment.p2 = Point.objects.get(trip=trip, place__id=data['p2_place'])
        segment.start_date=data['start_date']
        segment.end_date=data['end_date']
        segment.transportation_method = data['transportation_method']
        segment.save()

    def save(self):
        trip = super(TripEditForm, self).save()

        segments = list(trip.segment_set.all())
        points = list(trip.point_set.all())
        new_segments_data, new_points_data = self.cleaned_data['path']

        # add points
        for new_point_data in new_points_data:
            if not find(points, lambda p: p.place_id == new_point_data):
                self._create_point(trip, new_point_data)

        # add / edit segments
        segments_grouped = group_items(segments, Segment.places_equal)
        new_segments_data_grouped = \
            group_items(new_segments_data,
                        lambda a, b: self._get_places(a) == self._get_places(b))

        for new_group in new_segments_data_grouped:
            match = lambda g: g[0].places_equal(self._get_places(new_group[0]))
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

        # delete segments
        for segment in segments:
            if not find(new_segments_data,
                        lambda s: segment.places_equal(self._get_places(s))):
                # TODO: check for annotations
                segment.delete()

        # delete points
        for point in points:
            if point.place_id not in new_points_data:
                # TODO: check for annotations
                point.delete()

        return trip

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

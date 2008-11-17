from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils import html
from django.utils.safestring import mark_safe

from geopy.distance import distance

from backpacked.utils import Enum

class Country(models.Model):
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=100)

    class Admin:
        pass

    def __unicode__(self):
        return self.name

class AdministrativeDivision(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country)

    class Meta:
        unique_together = (('country', 'code'),)

    class Admin:
        pass

    def __unicode__(self):
        return self.name

class Place(models.Model):
    source = models.IntegerField() # 1 = manual, 2 = geonames
    code = models.IntegerField()
    name = models.CharField(max_length=100)
    name_ascii = models.CharField(max_length=100)
    country = models.ForeignKey(Country)
    administrative_division = models.ForeignKey(AdministrativeDivision, null=True)
    coords = models.PointField()

    class Admin:
        pass

    def __unicode__(self):
        return self.name

    @property
    def display_name(self):
        name = self.name
        if self.administrative_division:
            if self.name != self.administrative_division.name:
                name += ", %s" % self.administrative_division.name
        name += ", %s" % self.country.name
        return name

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40)
    key_expires = models.DateTimeField()
    name = models.CharField(max_length=50, blank=True)
    current_location = models.ForeignKey(Place, blank=True, null=True)
    about = models.TextField(blank=True)

    class Admin:
        pass

    def __unicode__(self):
        return self.user.username

Visibility = Enum({'PUBLIC': (1, "Everyone"),
                   'PRIVATE': (3, "Myself only")})

class Trip(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PUBLIC)

    class Admin:
        pass

    def __unicode__(self):
        return self.name

    @property
    def visibility_h(self):
        return Visibility.get_description(self.visibility)

    def is_visible_to(self, user):
        if self.visibility == Visibility.PRIVATE and self.user != user:
            return False
        else:
            return True

class Point(models.Model):
    trip = models.ForeignKey(Trip)
    place = models.ForeignKey(Place, null=True)
    name = models.CharField(max_length=100)
    coords = models.PointField()

    def __unicode__(self):
        return str(self.coords)

    @property
    def annotation_count(self):
        return self.annotation_set.all().count()

TransportationMethod = Enum([(0, "Unspecified"),
                             (1, "Train"),
                             (2, "Airplane"),
                             (3, "Walk"),
                             (4, "Bike"),
                             (5, "Car"),
                             (6, "Bus"),
                             (7, "Boat"),
                             (8, "Motorcycle")])

class Segment(models.Model):
    trip = models.ForeignKey(Trip)
    p1 = models.ForeignKey(Point, related_name="segments_out")
    p2 = models.ForeignKey(Point, related_name="segments_in")
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    transportation_method = models.IntegerField(choices=TransportationMethod.choices, default=0)
    order_rank = models.IntegerField()

    def __unicode__(self):
        return "%s - %s" % (self.p1, self.p2)

    def __cmp__(self, other):
        return cmp(self.order_rank, other.order_rank)

    @property
    def transportation_method_str(self):
        return TransportationMethod.get_description(self.transportation_method)

    @property
    def length(self):
        return distance(self.p1.coords.coords, self.p2.coords.coords).km

    @property
    def annotation_count(self):
        return self.annotation_set.all().count()

ContentType = Enum({'TEXT': (1, "Text"),
                    'URL': (2, "URL")})

class Annotation(models.Model):
    trip = models.ForeignKey(Trip)
    point = models.ForeignKey(Point, null=True)
    segment = models.ForeignKey(Segment, null=True)
    date = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=30)
    content_type = models.IntegerField(choices=ContentType.choices)
    content = models.TextField()
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PUBLIC)

    def __init__(self, trip_id, entity, entity_id):
        self.trip_id = trip_id
        if entity == 'point':
            self.point_id = entity_id
        elif entity == 'segment':
            self.segment_id = entity_id
        else:
            raise ValueError()

    @property
    def entity(self):
        if self.point_id:
            return 'point'
        elif self.segment_id:
            return 'segment'

    @property
    def entity_id(self):
        return self.point_id or self.segment_id

    @property
    def url(self):
        return ("/trip/%s/%s/%s/annotation/%s/"
                % (self.trip_id, self.entity, self.entity_id, self.id))

    def __unicode__(self):
        return self.title

    def is_visible_to(self, user):
        if self.visibility == Visibility.PRIVATE and self.user != user:
            return False
        else:
            return True

    def render_short(self):
        if self.content_type == TEXT:
            return mark_safe("<a href=\"%s\">%s</a>"
                             % (html.escape(self.url),
                                html.escape(self.title)))
        elif self.content_type == URL:
            return mark_safe("<a href=\"%s\">%s</a>"
                             % (html.escape(self.content),
                                html.escape(self.title)))

    def render(self):
        if self.content_type == TEXT:
            return self.content

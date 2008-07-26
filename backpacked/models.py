from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.utils import html
from django.utils.safestring import mark_safe

from lib.mock import Mock

class Place(models.Model):
    name = models.CharField(max_length=100)
    coords = models.PointField()

    class Admin:
        pass

    def __unicode__(self):
        return self.name

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

PUBLIC = 1
PROTECTED = 2
PRIVATE = 3
VISIBILITIES = ((PUBLIC, "Public"),
               (PROTECTED, "Protected"),
               (PRIVATE, "Private"))

class Trip(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    visibility = models.IntegerField(choices=VISIBILITIES, default=PUBLIC)

    class Admin:
        pass

    def __unicode__(self):
        return self.name

class Point(models.Model):
    trip = models.ForeignKey(Trip)
    place = models.ForeignKey(Place, null=True)
    name = models.CharField(max_length=100)
    coords = models.PointField()

    def __unicode__(self):
        return str(self.coords)

TRANSPORTATION_METHODS = ((0, "Unspecified"),
                          (1, "Train"),
                          (2, "Airplane"),
                          (3, "Walk"),
                          (4, "Bike"),
                          (5, "Car"))

class Segment(models.Model):
    trip = models.ForeignKey(Trip)
    p1 = models.ForeignKey(Point, related_name="segments_out")
    p2 = models.ForeignKey(Point, related_name="segments_in")
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    transportation_method = models.IntegerField(choices=TRANSPORTATION_METHODS)

    def __unicode__(self):
        return "%s - %s" % (self.p1, self.p2)

    def __cmp__(self, other):
        return cmp(self.start_date, other.start_date)

    def places_equal(self, other):
        if isinstance(other, tuple):
            return (self.p1.place_id, self.p2.place_id) == other
        else:
            return self.places_equal((other.p1.place_id, other.p2.place_id))

TEXT = 1
URL = 2
CONTENT_TYPES = ((TEXT, "Text"),
                 (URL, "URL"))

class Annotation(models.Model):
    trip = models.ForeignKey(Trip)
    point = models.ForeignKey(Point, null=True)
    segment = models.ForeignKey(Segment, null=True)
    date = models.DateTimeField()
    title = models.CharField(max_length=30)
    content_type = models.IntegerField(choices=CONTENT_TYPES)
    content = models.TextField()
    visibility = models.IntegerField(choices=VISIBILITIES, default=PUBLIC)

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

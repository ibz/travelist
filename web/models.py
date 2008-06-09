from django.contrib.auth.models import User
from django.contrib.gis.db import models

from lib.mock import Mock

class Location(models.Model):
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
    current_location = models.ForeignKey(Location, blank=True, null=True)
    about = models.TextField(blank=True)

    class Admin:
        pass

    def __unicode__(self):
        return self.user.username

class Trip(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()

    class Admin:
        pass

    def __unicode__(self):
        return self.name

class Point(models.Model):
    trip = models.ForeignKey(Trip)
    location = models.ForeignKey(Location, null=True)
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

    def __cmp__(self, other):
        return cmp(self.start_date, other.start_date)

    def locations_equal(self, other):
        if isinstance(other, tuple):
            return (self.p1.location_id, self.p2.location_id) == other
        else:
            return self.locations_equal((other.p1.location_id, other.p2.location_id))

TEXT = 1
CONTENT_TYPES = ((TEXT, "Text"))

class Annotation(object):
    point = models.ForeignKey(Point, null=True)
    segment = models.ForeignKey(Segment, null=True)
    content_type = models.IntegerField(choices=CONTENT_TYPES)
    content = models.TextField()

    def __unicode__(self):
        return self.content

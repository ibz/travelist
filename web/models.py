from django.contrib.auth.models import User
from django.contrib.gis.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    coords = models.PointField()

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40)
    key_expires = models.DateTimeField()
    name = models.CharField(max_length=50)
    current_location = models.ForeignKey(Location)
    about = models.TextField()

class Trip(models.Model):
    title = models.CharField(max_length=200)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

class Point(models.Model):
    location = models.ForeignKey(Location, null=True)
    coords = models.PointField()
    trip = models.ForeignKey(Trip)
    arrival_date = models.DateTimeField()
    departure_date = models.DateTimeField()

class Segment(models.Model):
    p1 = models.ForeignKey(Point, related_name="segments_out")
    p2 = models.ForeignKey(Point, related_name="segments_in")
    trip = models.ForeignKey(Trip)
    transportation = models.IntegerField()

class Annotation(object):
    CONTENT_TYPES = ()
    point = models.ForeignKey(Point, null=True)
    segment = models.ForeignKey(Segment, null=True)
    content_type = models.IntegerField()
    content = models.TextField()

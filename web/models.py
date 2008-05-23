from django.contrib.gis.db import models

class Location(models.Model):
    name = models.CharField(max_length=100)
    coords = models.PointField()

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
    content_type = models.IntegerField()
    content = models.TextField()

class PointAnnotation(models.Model, Annotation):
    point = models.ForeignKey(Point)

class SegmentAnnotation(models.Model, Annotation):
    segment = models.ForeignKey(Segment)

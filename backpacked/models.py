from django.contrib.auth.models import User
from django.contrib.gis.db import models

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

UserLevel = Enum([(1, "Basic"),
                  (2, "Pro")])

class UserProfile(models.Model):
    user = models.OneToOneField(User)
    level = models.IntegerField(choices=UserLevel.choices, default=UserLevel.BASIC)
    confirmation_key = models.CharField(max_length=40)
    email_confirmed = models.BooleanField(default=False)
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
    date_arrived = models.DateTimeField(blank=True, null=True)
    date_left = models.DateTimeField(blank=True, null=True)
    visited = models.BooleanField(default=False)
    order_rank = models.IntegerField()

    def __unicode__(self):
        return str(self.coords)

    def __cmp__(self, other):
        return cmp(self.order_rank, other.order_rank)

    @property
    def annotation_count(self):
        return self.annotation_set.all().count()

    @property
    def point_annotations(self):
        return self.annotation_set.filter(segment=False)

    @property
    def segment_annotations(self):
        return self.annotation_set.filter(segment=True)

ContentType = Enum({'TEXT': (1, "Text"),
                    'URL': (2, "URL"),
                    'EXTERNAL_PHOTOS': (3, "Photos")})

class Annotation(models.Model):
    trip = models.ForeignKey(Trip)
    point = models.ForeignKey(Point, blank=True, null=True)
    segment = models.BooleanField()
    date = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=30)
    content_type = models.IntegerField(choices=ContentType.choices)
    content = models.TextField()
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PUBLIC)

    class UI(object):
        all = {}

        class Meta(type):
            def __init__(cls, name, bases, dct):
                if hasattr(cls, 'content_type'):
                    Annotation.UI.all[cls.content_type] = cls

        __metaclass__ = Meta

        def __init__(self, annotation):
            self.annotation = annotation

        def render_short(self):
            raise NotImplementedError()

        def render(self):
            raise NotImplementedError()

        def render_content_input(self, name, value, attrs=None):
            raise NotImplementedError()

        def clean_content(self, content):
            raise NotImplementedError()

    @property
    def ui(self):
        if not self.UI.all:
            # make sure annotation types have been loaded
            from backpacked import annotationtypes
        return self.UI.all[self.content_type](self)

    def __unicode__(self):
        return self.title

    @property
    def content_type_h(self):
        return ContentType.get_description(self.content_type)

    @property
    def visibility_h(self):
        return Visibility.get_description(self.visibility)

    def is_visible_to(self, user):
        if self.visibility == Visibility.PRIVATE and self.user != user:
            return False
        else:
            return True

    @property
    def is_photos(self):
        return self.content_type == ContentType.EXTERNAL_PHOTOS

    @property
    def url(self):
        return "/trip/%s/annotation/%s/" % (self.trip.id, self.id)

    @property
    def parent_name(self):
        if not self.point:
            return ""
        name = self.point.name
        if self.segment:
            name += " - "
            try:
                p2 = self.trip.point_set.filter(order_rank__gt=self.point.order_rank).\
                                         order_by('order_rank')[0:1].get()
                name += p2.name
            except Point.DoesNotExist:
                name += "?"
        return name

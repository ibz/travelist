import os
from datetime import datetime
from PIL import Image
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.gis.db import models

from backpacked import utils

class Country(models.Model):
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "countries"

    def __unicode__(self):
        return self.name

class AdministrativeDivision(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country)

    class Meta:
        unique_together = (('country', 'code'),)

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

UserLevel = utils.Enum([(1, "Basic"),
                        (2, "Pro")])

def _get_profile_picture_location(profile, name):
    username = profile.user.username
    return "pp/%s/%s%s" % (username[0], username, os.path.splitext(name)[1])

class UserProfile(models.Model):
    PICTURE_MAX_SIZE = (125, 125) # NB: Don't forget to edit CSS when changing this!

    user = models.OneToOneField(User, primary_key=True)
    level = models.IntegerField(choices=UserLevel.choices, default=UserLevel.BASIC)
    confirmation_key = models.CharField(max_length=40)
    email_confirmed = models.BooleanField(default=False)
    name = models.CharField(max_length=50, blank=True)
    current_location = models.ForeignKey(Place, blank=True, null=True)
    about = models.TextField(blank=True)
    picture = models.ImageField(blank=True, upload_to=_get_profile_picture_location)

    def __unicode__(self):
        return self.user.username

    def save(self):
        super(UserProfile, self).save()
        if self.picture:
            image = Image.open(self.picture.path)
            for max in UserProfile.PICTURE_MAX_SIZE:
                for actual in image.size:
                    if actual > max:
                        image.thumbnail(UserProfile.PICTURE_MAX_SIZE)
                        image.save(self.picture.path)
                        return

RelationshipStatus = utils.Enum([(0, "Pending"),
                                 (1, "Confirmed")])

class UserRelationship(models.Model):
    class __metaclass__(models.Model.__metaclass__):
         def __init__(cls, name, bases, classdict):
             models.Model.__metaclass__.__init__(cls, name, bases, classdict)

             # extend django.contrib.auth.models.User class
             User.get_relationship = lambda self, other: \
                 UserRelationship.objects.get(Q(lhs=self, rhs=other) | Q(lhs=other, rhs=self))
             User.get_confirmed_relationships = lambda self: \
                 UserRelationship.objects.filter(Q(lhs=self) | Q(rhs=self), status=RelationshipStatus.CONFIRMED)
             def get_relationship_status(self, other):
                 is_self = self == other
                 if is_self:
                     is_friend = is_friend_pending = False
                 elif self.is_anonymous() or other.is_anonymous():
                     is_friend = is_friend_pending = False
                 else:
                     try:
                         relationship = self.get_relationship(other)
                         is_friend = relationship.status == RelationshipStatus.CONFIRMED
                         is_friend_pending = relationship.status == RelationshipStatus.PENDING
                     except UserRelationship.DoesNotExist:
                         is_friend = is_friend_pending = False
                 return is_self, is_friend, is_friend_pending
             User.get_relationship_status = get_relationship_status

    lhs = models.ForeignKey(User, related_name="userrelationship_lhs_set")
    rhs = models.ForeignKey(User, related_name="userrelationship_rhs_set")
    status = models.IntegerField(choices=RelationshipStatus.choices)
    date_confirmed = models.DateTimeField(null=True)
    lhs_notes = models.TextField()
    rhs_notes = models.TextField()

Visibility = utils.Enum({'PUBLIC': (1, "Everyone"),
                         'PROTECTED': (2, "Me and my friends"),
                         'PRIVATE': (3, "Myself only")})

class TripManager(models.Manager):
    def for_user(self, owner, viewer):
        is_self, is_friend, _ = owner.get_relationship_status(viewer)
        trips = self.filter(user=owner)
        if not is_self:
            if is_friend:
                trips = trips.filter(visibility__in=[Visibility.PUBLIC, Visibility.PROTECTED])
            else:
                trips = trips.filter(visibility=Visibility.PUBLIC)
        return trips

class Trip(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PUBLIC)
    objects = TripManager()

    class Meta:
        ordering = ['-start_date']

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

ContentType = utils.Enum({'TEXT': (1, "Text"),
                          'URL': (2, "URL"),
                          'EXTERNAL_PHOTOS': (3, "Photos"),
                          'TRANSPORTATION': (4, "Transportation"),
                          'GPS': (5, "GPS")})

class Annotation(models.Model):
    trip = models.ForeignKey(Trip)
    point = models.ForeignKey(Point, blank=True, null=True)
    segment = models.BooleanField()
    date = models.DateTimeField(blank=True, null=True)
    title = models.CharField(max_length=30)
    content_type = models.IntegerField(choices=ContentType.choices)
    content = models.TextField(null=True)
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PUBLIC)

    class Meta:
        ordering = ['content_type', 'point', 'segment', 'title']

    @property
    def manager(self):
        from backpacked import annotationtypes
        return annotationtypes.get_manager(self.content_type)(self)

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
    def url(self):
        return "/trips/%s/annotations/%s/" % (self.trip.id, self.id)

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

    def save(self):
        super(Annotation, self).save()
        self.manager.after_save()

class ExtendedAnnotationContent(models.Model):
    annotation = models.OneToOneField(Annotation, primary_key=True, related_name='extended_content')
    content = models.TextField()

NotificationType = utils.Enum({'FRIEND_REQUEST': (1, "Friend request"),
                               'TRIP_SHARE_REQUEST': (2, "Trip share request")})

class Notification(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(default=datetime.now)
    type = models.IntegerField(choices=NotificationType.choices)
    content = models.TextField()

    class Meta:
        ordering = ['-date']

    @property
    def manager(self):
        from backpacked import notificationtypes
        return notificationtypes.get_manager(self.type)(self)

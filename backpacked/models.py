import os
from datetime import date
from datetime import datetime

from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.gis.db import models

import settings

from backpacked import utils
from backpacked.utils import cached_property

class Country(models.Model):
    code = models.CharField(max_length=2)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "countries"

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.code)

class AdministrativeDivision(models.Model):
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country)

    class Meta:
        unique_together = ('country', 'code')

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.code)

class Place(models.Model):
    url_prefix = 'places'

    source = models.IntegerField() # 1 = manual, 2 = geonames
    external_code = models.IntegerField()
    name = models.CharField(max_length=100)
    name_ascii = models.CharField(max_length=100)
    country = models.ForeignKey(Country)
    administrative_division = models.ForeignKey(AdministrativeDivision, null=True)
    coords = models.PointField()
    wiki_content = models.TextField(blank=True)
    date_modified_external = models.DateTimeField(null=True)

    def __unicode__(self):
        return self.display_name

    def __cmp__(self, other):
        return cmp(self.name, other.name)

    def get_absolute_url(self):
        return "/places/%s-%s/" % (self.id, utils.clean_title_for_url(self.display_name))

    @cached_property
    def display_name(self):
        name = self.name
        if self.administrative_division:
            if self.name != self.administrative_division.name:
                name += ", %s" % self.administrative_division.name
        name += ", %s" % self.country.name
        return name

    @cached_property
    def ratings(self):
        counts = PlaceRating.objects.filter(place=self).values('value').annotate(models.Count('value'))
        ratings = {1: 0, 2: 0, 3: 0}
        ratings.update(dict([(c['value'], c['value__count']) for c in counts]))
        return ratings

class PlaceName(models.Model):
    place = models.ForeignKey(Place)
    source = models.IntegerField() # 1 = manual, 2 = geonames
    name = models.CharField(max_length=200, db_index=True)

class PlaceSuggestion(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=100)
    comments = models.TextField()

    def __unicode__(self):
        return self.name

class PlaceHist(models.Model):
    place = models.ForeignKey(Place)
    wiki_content = models.TextField()
    user = models.ForeignKey(User)
    date_added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.place.display_name

class PlaceRating(models.Model):
    place = models.ForeignKey(Place)
    user = models.ForeignKey(User)
    value = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

class PlaceComment(models.Model):
    place = models.ForeignKey(Place)
    user = models.ForeignKey(User)
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

class Accommodation(models.Model):
    url_prefix = 'accommodations'

    name = models.CharField(max_length=100)
    place = models.ForeignKey(Place, editable=False)
    wiki_content = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('name', 'place')

    def __unicode__(self):
        return "%s, %s" % (self.name, self.place.name)

    def get_absolute_url(self):
        title = utils.clean_title_for_url(self.name)
        return "/accommodations/%s%s%s/" % (self.id, "-" if title else "", title)

    @cached_property
    def ratings(self):
        counts = AccommodationRating.objects.filter(accommodation=self).values('value').annotate(models.Count('value'))
        ratings = {1: 0, 2: 0, 3: 0}
        ratings.update(dict([(c['value'], c['value__count']) for c in counts]))
        return ratings

class AccommodationHist(models.Model):
    accommodation = models.ForeignKey(Accommodation)
    wiki_content = models.TextField()
    user = models.ForeignKey(User)
    date_added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.accommodation.name

class AccommodationRating(models.Model):
    accommodation = models.ForeignKey(Accommodation)
    user = models.ForeignKey(User)
    value = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)

class AccommodationComment(models.Model):
    accommodation = models.ForeignKey(Accommodation)
    user = models.ForeignKey(User)
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']

UserLevel = utils.Enum([(1, "Basic"),
                        (2, "Pro")])

def _get_profile_picture_location(profile, name):
    username = profile.user.username
    return "pp/%s/%s%s" % (username[0], username, os.path.splitext(name)[1])

class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True)
    level = models.IntegerField(choices=UserLevel.choices, default=UserLevel.BASIC)
    confirmation_key = models.CharField(max_length=40)
    email_confirmed = models.BooleanField(default=False)
    name = models.CharField(max_length=50, blank=True)
    current_location = models.ForeignKey(Place, blank=True, null=True)
    about = models.TextField(blank=True)
    picture = models.ImageField(blank=True, upload_to=_get_profile_picture_location)
    twitter_username = models.CharField(max_length=40, blank=True, null=True, db_index=True, unique=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.user.username

    @property
    def picture_thumbnail_path(self):
        if self.picture:
            split = os.path.splitext(self.picture.path)
            return "".join([split[0], ".thumbnail", split[1]])

    @property
    def picture_thumbnail_url(self):
        if self.picture:
            try:
                dot_index = self.picture.url.rindex(".")
            except ValueError:
                return "%s.thumbnail" % self.picture.url
            return "%s.thumbnail%s" % (self.picture.url[:dot_index], self.picture.url[dot_index:])
        else:
            return "%spp/default.png" % settings.MEDIA_URL

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
             def get_friends(self):
                 relationships = self.get_confirmed_relationships()
                 friend_ids = [str(r.lhs_id) if r.lhs_id != self.id else str(r.rhs_id) for r in relationships]
                 return [p.user for p in UserProfile.objects.filter(user__in=friend_ids).select_related('user')]
             User.get_friends = get_friends
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

def is_visible(visibility, user, other):
    if visibility == Visibility.PUBLIC:
        return True
    elif visibility == Visibility.PROTECTED:
        if user == other:
            return True
        else:
            _, is_friend, _ = user.get_relationship_status(other)
            return is_friend
    elif visibility == Visibility.PRIVATE:
        return user == other
    else:
        raise ValueError()

class TripManager(models.Manager):
    def for_user(self, owner, viewer):
        trips = self.filter(user=owner)
        if owner != viewer:
            _, is_friend, _ = owner.get_relationship_status(viewer)
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
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    objects = TripManager()

    class Meta:
        ordering = ['-start_date']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        title = utils.clean_title_for_url(self.name)
        return "/trips/%s%s%s/" % (self.id, "-" if title else "", title)

    @property
    def status(self):
        if date.today() < self.start_date:
            return 'FUTURE'
        elif date.today() > self.end_date:
            return 'PAST'
        else:
            return 'CURRENT'

    @property
    def visibility_h(self):
        return Visibility.get_description(self.visibility)

    @property
    def visibility_name(self):
        return Visibility.get_name(self.visibility)

    def is_visible_to(self, user):
        return is_visible(self.visibility, self.user, user)

    def get_annotations_visible_to(self, user):
        if self.user == user:
            return self.annotation_set
        _, is_friend, _ = self.user.get_relationship_status(user)
        if is_friend:
            return self.annotation_set.filter(visibility__in=[Visibility.PUBLIC, Visibility.PROTECTED])
        else:
            return self.annotation_set.filter(visibility=Visibility.PUBLIC)

    @property
    def transportations(self):
        return sorted(list(set([(int(t.content), t.manager.display_name)
                                for t in self.annotation_set.filter(content_type=ContentType.TRANSPORTATION)
                                if int(t.content)])), key=lambda t: t[0])

    def copy(self, user):
        new_trip = Trip(user=user, name=self.name, start_date=self.start_date, end_date=self.end_date, visibility=Visibility.PUBLIC)
        new_trip.save()
        transportations = list(self.annotation_set.filter(content_type=ContentType.TRANSPORTATION))
        for p in self.point_set.all():
            new_point = Point(trip=new_trip, place=p.place, name=p.name, coords=p.coords,
                              date_arrived=p.date_arrived, date_left=p.date_left, visited=p.visited, order_rank=p.order_rank)
            new_point.save()
            transportation = Annotation(trip=new_trip, point=new_point, segment=True, title="", content_type=ContentType.TRANSPORTATION, visibility=Visibility.PUBLIC)
            transportation.content = utils.find(transportations, lambda t: t.point == p).content
            transportation.save()
        return new_trip

    def add_tweet(self, tweet):
        if Annotation.objects.filter(content_type=ContentType.TWEET, external_id=str(tweet['id'])).count() == 0:
            annotation = Annotation(trip=self, date=tweet['created_at'], title="", content_type=ContentType.TWEET)
            annotation.external_id = str(tweet['id'])
            annotation.content = tweet['text']
            annotation.visibility = Visibility.PUBLIC
            annotation.save()

class Point(models.Model):
    trip = models.ForeignKey(Trip)
    place = models.ForeignKey(Place, null=True)
    name = models.CharField(max_length=100)
    coords = models.PointField()
    date_arrived = models.DateTimeField(blank=True, null=True)
    date_left = models.DateTimeField(blank=True, null=True)
    visited = models.BooleanField(default=False)
    order_rank = models.IntegerField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order_rank']

    def __unicode__(self):
        return str(self.coords)

    def __cmp__(self, other):
        return cmp(self.order_rank, other.order_rank)

class TripLink(models.Model):
    lhs = models.ForeignKey(Trip, related_name="triplink_lhs_set")
    rhs = models.ForeignKey(Trip, related_name="triplink_rhs_set", null=True)
    start_place = models.ForeignKey(Place, related_name="triplink_start_place_set", null=True)
    end_place = models.ForeignKey(Place, related_name="triplink_end_place_set", null=True)
    status = models.IntegerField(choices=RelationshipStatus.choices)
    date_confirmed = models.DateTimeField(null=True)

ContentType = utils.Enum({'ACTIVITY': (1, "Activity"),
                          'URL': (2, "URL"),
                          'EXTERNAL_PHOTOS': (3, "Photos"),
                          'TRANSPORTATION': (4, "Transportation"),
                          'GPS': (5, "GPS"),
                          'ACCOMMODATION': (6, "Accommodation"),
                          'COST': (7, "Cost"),
                          'NOTE': (8, "Note"),
                          'TWEET': (9, "Tweet")})

class Annotation(models.Model):
    trip = models.ForeignKey(Trip)
    point = models.ForeignKey(Point, blank=True, null=True)
    segment = models.BooleanField()
    date = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=100)
    content_type = models.IntegerField(choices=ContentType.choices, db_index=True)
    external_id = models.CharField(max_length=30, null=True, blank=True, db_index=True)
    content = models.TextField(null=True)
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PUBLIC)
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['content_type', 'point', 'segment', 'date']

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
        return is_visible(self.visibility, self.trip.user, user) and is_visible(self.trip.visibility, self.trip.user, user)

    @property
    def url(self):
        return "/trips/%s/annotations/%s/" % (self.trip.id, self.id)

    def save(self):
        super(Annotation, self).save()
        self.manager.after_save()

class ExtendedAnnotationContent(models.Model):
    annotation = models.OneToOneField(Annotation, primary_key=True, related_name='extended_content')
    content = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

NotificationType = utils.Enum({'FRIEND_REQUEST': (1, "Friend request"),
                               'TRIP_LINK_REQUEST': (2, "Trip link request")})

class Notification(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(choices=NotificationType.choices)
    content = models.TextField()

    class Meta:
        ordering = ['-date']

    @property
    def manager(self):
        from backpacked import notificationtypes
        return notificationtypes.get_manager(self.type)(self)

SuggestionType = utils.Enum([(1, "Report issue"),
                             (2, "Suggest feature")])

class Suggestion(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    type = models.IntegerField(choices=SuggestionType.choices, default=SuggestionType.REPORT_ISSUE)
    comments = models.TextField()

    class Meta:
        ordering = ['-date']

BackgroundTaskType = utils.Enum({'PROCESS_TWEETS': (1, "Process tweets"),
                                 'PROCESS_TWEETS_REALTIME': (2, "Process tweets realtime")})
BackgroundTaskFrequency = utils.Enum({'HOURLY': (1, "Hourly")})

class BackgroundTask(models.Model):
    type = models.IntegerField(choices=BackgroundTaskType.choices)
    frequency = models.IntegerField(choices=BackgroundTaskFrequency.choices)
    parameters = models.TextField(null=True)
    state = models.TextField(null=True)

    @property
    def manager(self):
        from backpacked import backgroundtasktypes
        return backgroundtasktypes.get_manager(self.type)(self)

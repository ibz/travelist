import time

from django.utils import simplejson

from backpacked import models
from backpacked import utils
from backpacked.lib import flickr
from backpacked.lib import twitter

def get_manager(type):
    return BackgroundTaskManager.all[type]

class BackgroundTaskManager(object):
    all = {}

    class __metaclass__(type):
        def __init__(cls, name, bases, classdict):
            type.__init__(cls, name, bases, classdict)
            if hasattr(cls, 'type'):
                BackgroundTaskManager.all[cls.type] = cls

    def __init__(self, task=None):
        self.task = task

    def save_state(self, state):
        self.task.state = state
        self.task.save()

    def finish(self):
        self.task.delete()

def add_tweet(trip, tweet):
    if models.Annotation.objects.filter(content_type=models.ContentType.TWEET, external_id=str(tweet['id'])).count() == 0:
        annotation = models.Annotation(trip=trip, date=tweet['created_at'], title="", content_type=models.ContentType.TWEET)
        annotation.external_id = str(tweet['id'])
        annotation.content = annotation.manager.clean_content(tweet['text'])
        annotation.visibility = models.Visibility.PUBLIC
        annotation.save()

class ProcessTweetsManager(BackgroundTaskManager):
    type = models.BackgroundTaskType.PROCESS_TWEETS

    def run(self):
        user_id = int(self.task.parameters)
        max_id = self.task.state

        while True:
            limit = twitter.rate_limit()
            if limit:
                break
            time.sleep(5)

        user = models.User.objects.get(id=user_id)
        trips = list(user.trip_set.all())

        if not trips:
            self.finish()
            return

        page = 1
        while limit:
            tweets = twitter.user_timeline(user.userprofile.twitter_username, page=page, max_id=max_id)
            if not tweets:
                self.finish()
                return
            for tweet in tweets:
                date = tweet['created_at']
                if date.date() < trips[-1].start_date:
                    self.finish()
                    return
                trip = utils.find(trips, lambda t: t.start_date <= date.date() <= t.end_date)
                if trip:
                    add_tweet(trip, tweet)
            self.save_state(tweets[-1]['id'])
            limit -= 1
            page += 1
            time.sleep(1)

class ProcessTwitterRealtimeManager(BackgroundTaskManager):
    type = models.BackgroundTaskType.PROCESS_TWITTER_REALTIME

    def run(self):
        def process_tweet(tweet):
            try:
                twitter_username, date = tweet['user']['screen_name'], tweet['created_at']
                user = models.User.objects.get(userprofile__twitter_username=twitter_username)
                trip = profile.user.trip_set.filter(start_date__lte=date, end_date__gte=date)[0]
                add_tweet(trip, tweet)
            except models.User.DoesNotExist, IndexError:
                pass

        twitter.track("#trip", process_tweet)

def add_flickr_photo(trip, photo):
    if models.Annotation.objects.filter(content_type=models.ContentType.FLICKR_PHOTO, external_id=str(photo['id'])).count() == 0:
        details = flickr.flickr_photos_getInfo(photo['id'])
        urls = flickr.flickr_photos_getSizes(photo['id'])
        annotation = models.Annotation(trip=trip, date=details['date'], title=details['title'], content_type=models.ContentType.FLICKR_PHOTO)
        annotation.external_id = str(photo['id'])
        annotation.content = simplejson.dumps({'url': details['url'], 'thumbnail': urls['Thumbnail'], 'normal': urls['Medium']})
        annotation.visibility = models.Visibility.PUBLIC
        annotation.save()

class ProcessFlickrRealtimeManager(BackgroundTaskManager):
    type = models.BackgroundTaskType.PROCESS_FLICKR_REALTIME

    def run(self):
        def process_tag(value):
            trip_id = int(value)
            try:
                trip = models.Trip.objects.get(id=trip_id)
                user_id = trip.user.userprofile.flickr_userid
                if not user_id:
                    return
                photos = flickr.flickr_photos_search(user_id=user_id, tags="backpacked:trip=%s" % trip_id)
                for photo in photos:
                    add_flickr_photo(trip, photo)
            except models.Trip.DoesNotExist:
                pass

        flickr.track("backpackedit", "trip", process_tag)

import time

from backpacked import models
from backpacked import utils
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
                    trip.add_tweet(tweet)
            self.save_state(tweets[-1]['id'])
            limit -= 1
            page += 1
            time.sleep(1)

class ProcessTweetsRealtimeManager(BackgroundTaskManager):
    type = models.BackgroundTaskType.PROCESS_TWEETS_REALTIME

    def run(self):
        def process_tweet(tweet):
            try:
                twitter_username, date = tweet['user']['screen_name'], tweet['created_at']
                user = models.User.objects.get(userprofile__twitter_username=twitter_username)
                trip = profile.user.trip_set.filter(start_date__lte=date, end_date__gte=date)[0]
                trip.add_tweet(tweet)
            except models.User.DoesNotExist, IndexError:
                pass

        twitter.track("#trip", process_tweet)

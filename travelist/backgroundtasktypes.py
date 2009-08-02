import time

from travelist import models
from travelist import utils
from travelist.lib import twitter

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
                    if models.Annotation.objects.filter(content_type=models.ContentType.TWEET, external_id=str(tweet['id'])).count() == 0:
                        annotation = models.Annotation(trip=trip, date=tweet['created_at'], title="", content_type=models.ContentType.TWEET)
                        annotation.external_id = str(tweet['id'])
                        annotation.content = annotation.manager.clean_content(tweet['text'])
                        annotation.save()
            self.save_state(tweets[-1]['id'])
            limit -= 1
            page += 1
            time.sleep(1)

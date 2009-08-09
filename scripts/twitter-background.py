#!/usr/bin/python

import os
import sys
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from travelist import models
from travelist.lib import twitter

def add_tweet(trip, tweet):
    if models.Annotation.objects.filter(content_type=models.ContentType.TWEET, external_id=str(tweet['id'])).count() == 0:
        annotation = models.Annotation(trip=trip, date=tweet['created_at'], title="", content_type=models.ContentType.TWEET)
        annotation.external_id = str(tweet['id'])
        annotation.content = annotation.manager.clean_content(tweet['text'])
        annotation.save()

def process_tweet(tweet):
    try:
        twitter_username, date = tweet['user']['screen_name'], tweet['created_at']
        user = models.User.objects.get(userprofile__twitter_username=twitter_username)
        trip = profile.user.trip_set.filter(start_date__lte=date, end_date__gte=date)[0]
    except models.User.DoesNotExist, IndexError:
        return
    except Exception:
        traceback.print_exc()
        raise
    try:
        add_tweet(trip, tweet)
    except Exception:
        traceback.print_exc()
        raise

twitter.track("#trip", process_tweet)

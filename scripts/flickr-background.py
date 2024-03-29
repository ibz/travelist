#!/usr/bin/python

import os
import sys
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from django.utils import simplejson

from travelist import models
from travelist.lib import flickr

def add_flickr_photo(trip, photo):
    if models.Annotation.objects.filter(content_type=models.ContentType.FLICKR_PHOTO, external_id=str(photo['id'])).count() == 0:
        details = flickr.flickr_photos_getInfo(photo['id'])
        urls = flickr.flickr_photos_getSizes(photo['id'])
        annotation = models.Annotation(trip=trip, date=details['date'], title=details['title'], content_type=models.ContentType.FLICKR_PHOTO)
        annotation.external_id = str(photo['id'])
        annotation.content = simplejson.dumps({'url': details['url'], 'thumbnail': urls['Thumbnail'], 'normal': urls['Medium']})
        annotation.visibility = models.Visibility.PUBLIC
        annotation.save()

def process_tag(value):
    try:
        trip_id = int(value)
        trip = models.Trip.objects.get(id=trip_id)
    except ValueError, models.Trip.DoesNotExist:
        return
    except Exception:
        traceback.print_exc()
        raise
    try:
        user_id = trip.user.userprofile.flickr_userid
        if not user_id:
            return
        photos = flickr.flickr_photos_search(user_id=user_id, tags="travelist:trip=%s" % trip_id)
        for photo in photos:
            add_flickr_photo(trip, photo)
    except Exception:
        traceback.print_exc()
        raise

flickr.track("travelist", "trip", process_tag)

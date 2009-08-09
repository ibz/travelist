from datetime import datetime
import time
import traceback
import urllib
import urllib2
from xml.dom import minidom

from django.core import mail

from travelist import utils

import settings

def call(method, **params):
    response = urllib2.urlopen("http://flickr.com/services/rest?api_key=%s&method=%s&%s"
                               % (settings.FLICKR_KEY, method, urllib.urlencode(params)))
    try:
        return minidom.parse(response)
    finally:
        response.close()

def flickr_machinetags_getRecentValues(namespace, predicate, added_since):
    dom = call('flickr.machinetags.getRecentValues', namespace=namespace, predicate=predicate, added_since=added_since)
    return [{'value': node.childNodes[0].nodeValue,
             'last_added': int(node.getAttribute('last_added'))}
            for node in dom.getElementsByTagName('value')]

def flickr_photos_search(user_id, tags):
    dom = call('flickr.photos.search', user_id=user_id, tags=tags)
    return [{'id': int(node.getAttribute('id')),
             'owner': node.getAttribute('owner')}
            for node in dom.getElementsByTagName('photo')]

def flickr_photos_getInfo(photo_id):
    dom = call('flickr.photos.getInfo', photo_id=photo_id)
    try:
        return [{'title': node.getElementsByTagName('title')[0].childNodes[0].nodeValue,
                 'date': datetime.strptime(node.getElementsByTagName('dates')[0].getAttribute('taken'), "%Y-%m-%d %H:%M:%S"),
                 'url': utils.find(node.getElementsByTagName('url'), lambda n: n.getAttribute('type') == 'photopage').childNodes[0].nodeValue}
                for node in dom.getElementsByTagName('photo')][0]
    except IndexError:
        return None

def flickr_photos_getSizes(photo_id):
    dom = call('flickr.photos.getSizes', photo_id=photo_id)
    return dict((node.getAttribute('label'), node.getAttribute('source'))
                for node in dom.getElementsByTagName('size'))

def track(namespace, predicate, callback):
    wait_time = 60
    last_added_max = 0
    while True:
        try:
            values = flickr_machinetags_getRecentValues(namespace, predicate, last_added_max + 1)
            wait_time = 60
            for value in values:
                callback(value['value'])
                if value['last_added'] > last_added_max:
                    last_added_max = value['last_added']
            time.sleep(60)
        except Exception:
            traceback.print_exc()
            time.sleep(wait_time)
            wait_time *= 2
            if wait_time > 10 * 60:
                mail.mail_admins("Flickr tracking error", traceback.format_exc(), fail_silently=True)
                wait_time = 10 * 60

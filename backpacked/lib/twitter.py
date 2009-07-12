import base64
import calendar
from datetime import datetime
import rfc822
import time
import traceback
import urllib
import urllib2

from django.core import mail

from django.utils import simplejson

import settings

def rate_limit():
    response = urllib2.urlopen("http://twitter.com/account/rate_limit_status.json")
    try:
        return simplejson.loads(response.read())['remaining_hits']
    except:
        return 0
    finally:
        response.close()

def cleanup_status(status):
    status['created_at'] = datetime.fromtimestamp(calendar.timegm(rfc822.parsedate(status['created_at'])))
    return status

def user_timeline(screen_name, page, count=200, max_id=None):
    params = {'screen_name': screen_name, 'page': page, 'count': count}
    if max_id:
        params['max_id'] = max_id
    response = urllib2.urlopen("http://twitter.com/statuses/user_timeline.json?" + urllib.urlencode(params))
    try:
        return [cleanup_status(s) for s in simplejson.loads(response.read()) if not s['in_reply_to_status_id']]
    except:
        return []
    finally:
        response.close()

def track(keyword, callback):
    wait_time = 1
    while True:
        try:
            request = urllib2.Request("http://stream.twitter.com/track.json?%s" % urllib.urlencode({'track': keyword}))
            header = "Basic %s" % base64.encodestring('%s:%s' % (settings.TWITTER_USERNAME, settings.TWITTER_PASSWORD))
            request.add_header("Authorization", header)
            f = urllib2.urlopen(request)
            wait_time = 1
            while True:
                line = f.readline().strip()
                if line:
                    status = cleanup_status(simplejson.loads(line))
                    callback(status)
        except:
            time.sleep(wait_time)
            wait_time *= 2
            if wait_time > 5 * 60:
                mail.mail_admins("Twitter tracking error", traceback.format_exc(), fail_silently=True)
                wait_time = 5 * 60

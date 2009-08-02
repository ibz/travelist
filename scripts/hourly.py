#!/usr/bin/python

import os
import sys
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from django.core import mail

from travelist import models

try:
    task = models.BackgroundTask.objects.filter(frequency=models.BackgroundTaskFrequency.HOURLY).order_by('id')[0]
except IndexError:
    task = None

if task:
    try:
        task.manager.run()
    except:
        mail.mail_admins("Hourly task error", traceback.format_exc(), fail_silently=True)

import sha
from datetime import datetime
from datetime import timedelta
from random import random

from django import newforms as forms
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.decorators import login_required

from web.models import UserProfile
from web.forms import AccountDetailsForm
from web.forms import AccountRegistrationForm

import settings

def render(template, context=None):
    if not context:
        context = {}
    context['settings'] = settings
    return render_to_response(template, context)

def index(request):
    return render("web/index.html")

@transaction.commit_on_success
def account_register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    if request.POST:
        user = User(is_staff=False, is_superuser=False, is_active=False)
        form = RegistrationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()

            salt = sha.new(str(random())).hexdigest()[:5]
            activation_key = sha.new(salt + user.username).hexdigest()
            key_expires = datetime.today() + timedelta(2)
            profile = UserProfile(user=user,
                                  activation_key=activation_key,
                                  key_expires=key_expires)
            profile.save()

            email_subject = "Your new %s account confirmation" % settings.SITE_NAME
            email_body = "Hello, %s, and thanks for signing up for an %s account!\n\nTo activate your account, click this link within 48 hours:\n\n%s/account/confirm/%s" % (
                user.username,
                settings.SITE_NAME,
                settings.SITE_URL,
                profile.activation_key)
            send_mail(email_subject,
                      email_body,
                      settings.CUSTOMER_EMAIL,
                      [user.email])
            return render("web/account_register.html", {'created': True})
    else:
        form = RegistrationForm()
    return render("web/account_register.html", {'form': form})

def account_confirm(request, activation_key):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)
    if user_profile.key_expires < datetime.today():
        return render("web/account_confirm.html", {'expired': True})
    user = user_profile.user
    user.is_active = True
    user.save()
    return render("web/account_confirm.html", {'success': True})

@login_required
def account_details(request):
    if request.POST:
        form = AccountDetailsForm(request.POST)
    else:
        form = AccountDetailsForm()

    return render("web/account_details.html", {'form': form})

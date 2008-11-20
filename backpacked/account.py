import sha
from datetime import datetime
from datetime import timedelta
from random import random

from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.db.transaction import commit_on_success
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import accountui
from backpacked import models
from backpacked import utils
from backpacked import views

import settings

@require_POST
def login(request):
    user = auth.authenticate(username=request.POST['username'],
                             password=request.POST['password'])
    if not user.is_active:
        return http.HttpResponseRedirect("/")
    auth.login(request, user)
    return http.HttpResponseRedirect("/")

@require_GET
def logout(request):
    auth.logout(request)
    return http.HttpResponseRedirect("/")

def register_GET(request):
    form = accountui.AccountRegistrationForm()
    return views.render("account_register.html", request, {'form': form})

def register_POST(request):
    user = auth.models.User(is_staff=False, is_superuser=False, is_active=False)
    form = accountui.AccountRegistrationForm(request.POST, instance=user)
    if form.is_valid():
        user = form.save()

        salt = sha.new(str(random())).hexdigest()[:5]
        activation_key = sha.new(salt + user.username).hexdigest()
        key_expires = datetime.today() + timedelta(2)
        profile = models.UserProfile(user=user,
                                     activation_key=activation_key,
                                     key_expires=key_expires)
        profile.save()

        email_subject = "Your new backpacked.it account confirmation"
        email_body = (
"""Hello %s and thanks for signing up for a backpacked.it account!
To activate your account click this link within 48 hours:
http://backpacked.it/account/activate/%s/""" % (
                user.username,
                profile.activation_key))
        mail.send_mail(email_subject,
                       email_body,
                       settings.CUSTOMER_EMAIL,
                       [user.email])
        return views.render("account_register.html", request, {'created': True})
    else:
        return views.render("account_register.html", request, {'form': form})

@commit_on_success
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated():
        return http.HttpResponseRedirect("/")
    if request.method == 'GET':
        return register_GET(request)
    elif request.method == 'POST':
        return register_POST(request)

@require_GET
def activate(request, activation_key):
    user_profile = shortcuts.get_object_or_404(models.UserProfile, activation_key=activation_key)
    if user_profile.key_expires < datetime.today():
        return views.render("account_activate.html", request, {'expired': True})
    user = user_profile.user
    user.is_active = True
    user.save()
    return views.render("account_activate.html", request, {'success': True})

def details_GET(request):
    form = accountui.AccountDetailsForm(instance=request.user.get_profile())
    return views.render("account_details.html", request, {'form': form})

def details_POST(request):
    form = accountui.AccountDetailsForm(request.POST, instance=request.user.get_profile())
    if form.is_valid():
        form.save()
        return http.HttpResponseRedirect("/")
    else:
        return views.render("account_details.html", request, {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def details(request):
    if request.method == 'GET':
        return details_GET(request)
    else:
        return details_POST(request)

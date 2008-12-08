import sha
from datetime import datetime
from datetime import timedelta
from random import random

from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.db.models import Q
from django.db.transaction import commit_on_success
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import accountui
from backpacked import models
from backpacked import utils
from backpacked import views

import settings

def login_GET(request):
    return views.render("account_login.html", request, {'login_form': accountui.LoginForm()})

def login_POST(request):
    user = auth.authenticate(username=request.POST['username'],
                             password=request.POST['password'])
    if not user.is_active:
        return http.HttpResponseRedirect("/")
    auth.login(request, user)
    return http.HttpResponseRedirect("/")

@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == 'GET':
        return login_GET(request)
    elif request.method == 'POST':
        return login_POST(request)

@require_GET
def logout(request):
    auth.logout(request)
    return http.HttpResponseRedirect("/")

def register_GET(request):
    form = accountui.RegistrationForm()
    return views.render("account_register.html", request, {'form': form})

def register_POST(request):
    user = auth.models.User(is_staff=False, is_superuser=False, is_active=True)
    form = accountui.RegistrationForm(request.POST, instance=user)
    if form.is_valid():
        user = form.save()

        salt = sha.new(str(random())).hexdigest()[:5]
        confirmation_key = sha.new(salt + user.username).hexdigest()
        profile = models.UserProfile(user=user, confirmation_key=confirmation_key)
        profile.save()

        email_subject = "Your new backpacked.it account confirmation"
        email_body = (
"""Hello %(user)s and thanks for signing up for a backpacked.it account!
To confirm your email address click this link:
http://backpacked.it/account/confirm-email/?username=%(user)s&key=%(key)s""" % (
                {'user': user.username,
                 'key': profile.confirmation_key}))
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
def confirm_email(request):
    username = request.GET['username']
    key = request.GET['key']
    user_profile = shortcuts.get_object_or_404(models.UserProfile, user__username=username, confirmation_key=key)
    user_profile.email_confirmed = True
    user_profile.save()
    return views.render("account_confirmed_email.html", request)

def profile_GET(request):
    form = accountui.ProfileForm(instance=request.user.get_profile())
    return views.render("account_profile.html", request, {'form': form})

def profile_POST(request):
    form = accountui.ProfileForm(request.POST, request.FILES, instance=request.user.get_profile())
    if form.is_valid():
        form.save()
        return http.HttpResponseRedirect("/")
    else:
        return views.render("account_profile.html", request, {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    if request.method == 'GET':
        return profile_GET(request)
    else:
        return profile_POST(request)

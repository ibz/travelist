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
    return views.render("account_login.html", request, {'login_form': accountui.AccountLoginForm()})

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
    form = accountui.AccountRegistrationForm()
    return views.render("account_register.html", request, {'form': form})

def register_POST(request):
    user = auth.models.User(is_staff=False, is_superuser=False, is_active=True)
    form = accountui.AccountRegistrationForm(request.POST, instance=user)
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
http://backpacked.it/account/confirm-email/%(user)s/?key=%(key)s""" % (
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
def confirm_email(request, username):
    key = request.GET['key']
    user_profile = shortcuts.get_object_or_404(models.UserProfile, user__username=username, confirmation_key=key)
    user_profile.email_confirmed = True
    return views.render("account_confirmed_email.html", request)

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

@require_GET
def profile(request, username):
    profile = models.UserProfile.objects.filter(user__username=username).select_related('user').get()
    user = profile.user
    is_self = user == request.user
    if is_self:
        is_friend = is_friend_pending = False
    else:
        try:
            relationship = user.get_relationship(request.user)
            is_friend = relationship.status == models.RelationshipStatus.CONFIRMED
            is_friend_pending = relationship.status == models.RelationshipStatus.PENDING
        except models.UserRelationship.DoesNotExist:
            is_friend = is_friend_pending = False

    trips = models.Trip.objects.filter(user=user)
    if not is_self:
        if is_friend:
            trips = trips.filter(visibility__in=[models.Visibility.PUBLIC,
                                                 models.Visibility.PROTECTED])
        else:
            trips = trips.filter(visibility=models.Visibility.PUBLIC)
    trips = trips[0:5]
    return views.render("account_profile.html", request, {'profile': profile, 'is_self': is_self,
                                                          'is_friend': is_friend, 'is_friend_pending': is_friend_pending,
                                                          'trips': trips})

import sha
from datetime import datetime
from datetime import timedelta
from random import random

from django import newforms as forms
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from web.models import Location
from web.models import Trip
from web.models import Point
from web.models import Segment
from web.models import UserProfile
from web.forms import SegmentInput
from web.forms import AccountDetailsForm
from web.forms import AccountRegistrationForm
from web.forms import TripEditForm

import settings

def render(template, request, context=None):
    if not context:
        context = {}
    context['settings'] = settings
    return render_to_response(template, context, context_instance=RequestContext(request))

def index(request):
    return render("web/index.html", request)

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
            email_body = (
"""Hello, %s, and thanks for signing up for an %s account!
To activate your account, click this link within 48 hours:
%s/account/confirm/%s""" % (
                user.username,
                settings.SITE_NAME,
                settings.SITE_URL,
                profile.activation_key))
            send_mail(email_subject,
                      email_body,
                      settings.CUSTOMER_EMAIL,
                      [user.email])
            return render("web/account_register.html", request, {'created': True})
    else:
        form = RegistrationForm()
    return render("web/account_register.html", request, {'form': form})

def account_confirm(request, activation_key):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)
    if user_profile.key_expires < datetime.today():
        return render("web/account_confirm.html", request, {'expired': True})
    user = user_profile.user
    user.is_active = True
    user.save()
    return render("web/account_confirm.html", request, {'success': True})

@login_required
def account_details(request):
    if request.POST:
        form = AccountDetailsForm(request.POST, instance=request.user.get_profile())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/account/details/")
    else:
        form = AccountDetailsForm(instance=request.user.get_profile())

    return render("web/account_details.html", request, {'form': form})

@login_required
def trip_list(request):
    trips = Trip.objects.filter(user=request.user).order_by('start_date')
    return render("web/trip_list.html", request, {'trips': trips})

def trip_view(request, id):
    trip = get_object_or_404(Trip, id=id)
    return render("web/trip_view.html", request, {'trip': trip})

@login_required
def trip_edit(request, id):
    if id:
        trip = get_object_or_404(Trip, id=id, user=request.user)
    else:
        trip = Trip(user=request.user)
    if request.POST:
        form = TripEditForm(request.POST, instance=trip)
        if form.is_valid():
            trip = form.save()
            return HttpResponseRedirect("/trip/%s/" % trip.id)
    else:
        form = TripEditForm(instance=trip)
    return render("web/trip_edit.html", request,
                  {'trip': trip,
                   'form': form})

@login_required
def widget_segment_input(request):
    if request.GET:
        return HttpResponse(SegmentInput().render(request.GET['name'], None))

@login_required
def location_search(request):
    if request.GET:
        res = Location.objects.filter(name__icontains=request.GET['q'])[:5]
        return HttpResponse("\n".join(["%s|%s" % (l.name, l.id) for l in res]))

@login_required
def annotation_list(request):
    pass

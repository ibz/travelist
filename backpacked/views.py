import sha
from datetime import datetime
from datetime import timedelta
from random import random

from django import forms
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponseBadRequest
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from backpacked.models import Annotation
from backpacked.models import Place
from backpacked.models import Trip
from backpacked.models import Point
from backpacked.models import Segment
from backpacked.models import UserProfile
from backpacked.models import Visibility
from backpacked.forms import AnnotationEditForm
from backpacked.forms import AnnotationNewForm
from backpacked.forms import ContentInput
from backpacked.forms import AccountLoginForm
from backpacked.forms import AccountDetailsForm
from backpacked.forms import AccountRegistrationForm
from backpacked.forms import TripEditForm
from backpacked.forms import SegmentEditForm

import settings

def render(template, request, context=None):
    if not context:
        context = {}
    context['settings'] = settings
    return render_to_response(template, context, context_instance=RequestContext(request))

def index(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/trip/list/")
    else:
        return render("index.html", request,
                      {'login_form': AccountLoginForm()})

def account_login(request):
    if request.POST:
        user = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
        login(request, user)
        return HttpResponseRedirect("/")

def account_logout(request):
    logout(request)
    return HttpResponseRedirect("/")

@transaction.commit_on_success
def account_register(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/")
    if request.POST:
        user = User(is_staff=False, is_superuser=False, is_active=False)
        form = AccountRegistrationForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()

            salt = sha.new(str(random())).hexdigest()[:5]
            activation_key = sha.new(salt + user.username).hexdigest()
            key_expires = datetime.today() + timedelta(2)
            profile = UserProfile(user=user,
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
            send_mail(email_subject,
                      email_body,
                      settings.CUSTOMER_EMAIL,
                      [user.email])
            return render("account_register.html", request, {'created': True})
    else:
        form = AccountRegistrationForm()
    return render("account_register.html", request, {'form': form})

def account_activate(request, activation_key):
    user_profile = get_object_or_404(UserProfile, activation_key=activation_key)
    if user_profile.key_expires < datetime.today():
        return render("account_activate.html", request, {'expired': True})
    user = user_profile.user
    user.is_active = True
    user.save()
    return render("account_activate.html", request, {'success': True})

@login_required
def account_details(request):
    if request.POST:
        form = AccountDetailsForm(request.POST, instance=request.user.get_profile())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/")
    else:
        form = AccountDetailsForm(instance=request.user.get_profile())

    return render("account_details.html", request, {'form': form})

@login_required
def trip_list(request):
    trips = Trip.objects.filter(user=request.user).order_by('start_date')
    return render("trip_list.html", request, {'trips': trips})

def trip_view(request, id):
    trip = get_object_or_404(Trip, id=id)
    if trip.visibility == Visibility.PRIVATE:
        if trip.user != request.user:
            raise Http404()
    segments = sorted(list(trip.segment_set.all()))
    points = []
    for segment in segments:
        if segment.p1 not in points:
            points.append(segment.p1)
        if segment.p2 not in points:
            points.append(segment.p2)
    return render("trip_view.html", request,
                  {'trip': trip,
                   'segments': segments,
                   'points': points})

@login_required
def trip_edit(request, id=None):
    if id:
        trip = get_object_or_404(Trip, id=id, user=request.user)
    else:
        trip = Trip(user=request.user)
    if request.POST:
        form = TripEditForm(request.POST, instance=trip)
        if form.is_valid():
            trip = form.save()
            if id:
                return HttpResponseRedirect("/trip/%s/" % trip.id)
            else:
                return HttpResponseRedirect("/trip/%s/edit/create-segments/" % trip.id)
    else:
        form = TripEditForm(instance=trip)
    return render("trip_edit.html", request,
                  {'trip': trip,
                   'form': form})

@login_required
def trip_create_segments(request, id):
    trip = get_object_or_404(Trip, id=id, user=request.user)
    assert len(list(trip.segment_set.all())) == 0
    assert len(list(trip.point_set.all())) == 0
    if request.method == 'GET':
        return render("trip_create_segments.html", request)
    elif request.method == 'POST':
        place_ids = [int(request.POST[unicode(pid)])
                     for pid in sorted([int(pid)
                                        for pid in request.POST.keys()])]
        points = []
        for place_id in place_ids:
            place = Place.objects.get(id=place_id)
            point = Point(trip=trip, place=place, name=place.name, coords=place.coords)
            point.save()
            points.append(point)
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            segment = Segment(trip=trip, p1=p1, p2=p2, order_rank=i)
            segment.save()
        return HttpResponseRedirect("/trip/%s/" % trip.id)

@login_required
def trip_delete(request, id):
    trip = get_object_or_404(Trip, id=id, user=request.user)
    trip.delete()
    return HttpResponseRedirect("/trip/list/")

@login_required
def segment_edit(request, trip_id, id):
    segment = get_object_or_404(Segment, id=id, trip__user=request.user)
    if request.POST:
        form = SegmentEditForm(request.POST, instance=segment)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/trip/%s/" % trip_id)
    else:
        form = SegmentEditForm(instance=segment)
    return render("segment_edit.html", request,
                  {'trip_id': trip_id,
                   'segment': segment,
                   'form': form})

def widget_content_input(request):
    if request.GET:
        content_type = int(request.GET['content_type'])
        content_type_selector = request.GET['content_type_selector']
        name = request.GET['name']
        input = ContentInput(content_type, content_type_selector)
        return HttpResponse(input.render(name, None))
    else:
        return HttpResponseBadRequest()

def place_search(request):
    if request.GET:
        res = Place.objects.filter(name_ascii__istartswith=request.GET['q'])[:10]
        return HttpResponse("\n".join(["%s|%s" % (l.display_name, l.id) for l in res]))
    else:
        return HttpResponseBadRequest()

def annotation_view(request, trip_id, entity, entity_id, id):
    annotation = get_object_or_404(Annotation, id=id)
    if annotation.visibility == Visibility.PRIVATE:
        if annotation.trip.user != request.user:
            raise Http404()
    return render("annotation_view.html", request,
                  {'annotation': annotation})

@login_required
def annotation_edit(request, trip_id, entity, entity_id, id=None):
    form_class = id and AnnotationEditForm or AnnotationNewForm
    if id:
        annotation = get_object_or_404(Annotation, id=id)
    else:
        annotation = Annotation(trip_id=trip_id)
        if entity == 'point':
            annotation.point_id = entity_id
        elif entity == 'segment':
            annotation.segment_id = entity_id
        else:
            return HttpResponseBadRequest()
    if request.POST:
        form = form_class(request.POST, instance=annotation)
        if form.is_valid():
            annotation = form.save()
            return HttpResponseRedirect("/trip/%s/" % trip_id)
    else:
        form = form_class(instance=annotation)
    return render("annotation_edit.html", request,
                  {'trip_id': trip_id,
                   'annotation': annotation,
                   'form': form})

@login_required
def annotation_delete(request, trip_id, entity, entity_id, id):
    annotation = get_object_or_404(Annotation, id=id, trip__user=request.user)

    annotation.delete()
    return HttpResponseRedirect("/trip/%s/%s/%s/annotation/list/"
                                % (trip_id, entity, entity_id))

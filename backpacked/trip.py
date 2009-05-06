import re

from geopy.distance import distance

from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import annotationtypes
from backpacked import tripui
from backpacked import models
from backpacked import utils
from backpacked import views

@require_GET
def user(request, username):
    for_user = models.User.objects.get(username=username)
    trips = models.Trip.objects.for_user(owner=for_user, viewer=request.user)
    return views.render("trip_list.html", request, {'trips': trips, 'is_self': for_user == request.user,
                                                    'for_user': for_user})

def new_GET(request, trip):
    form = tripui.EditForm(instance=trip)
    return views.render("trip_edit.html", request, {'trip': trip, 'form': form})

def new_POST(request, trip):
    form = tripui.EditForm(request.POST, instance=trip)
    if form.is_valid():
        trip = form.save()
        return http.HttpResponseRedirect("/trips/%s/" % trip.id)
    else:
        return views.render("trip_edit.html", request, {'trip': trip, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def new(request):
    trip = models.Trip(user=request.user)
    if request.method == 'GET':
        return new_GET(request, trip)
    elif request.method == 'POST':
        return new_POST(request, trip)

@require_GET
def view(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    if not trip.is_visible_to(request.user):
        raise http.Http404()
    return views.render("trip.html", request, {'trip': trip})

def edit_GET(request, trip):
    form = tripui.EditForm(instance=trip)
    return views.render("trip_edit.html", request, {'trip': trip, 'form': form})

def edit_POST(request, trip):
    form = tripui.EditForm(request.POST, instance=trip)
    if form.is_valid():
        trip = form.save()
        return http.HttpResponseRedirect("/trips/%s/" % trip.id)
    else:
        return views.render("trip_edit.html", request, {'trip': trip, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    if request.method == 'GET':
        return edit_GET(request, trip)
    elif request.method == 'POST':
        return edit_POST(request, trip)

@require_GET
def details(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    if not trip.is_visible_to(request.user):
        raise http.Http404()

    points = dict([(p.id, {'id': p.id, 'place_id': p.place_id, 'name': p.name, 'coords': p.coords.coords,
                           'date_arrived': p.date_arrived, 'date_left': p.date_left, 'visited': p.visited,
                           'order_rank': p.order_rank,
                           'annotations': {'POINT': {}, 'SEGMENT': {}}})
                   for p in trip.point_set.all()])

    annotations = list(trip.get_annotations_visible_to(request.user).all())
    for annotation in annotations:
        if not annotation.point_id:
            continue
        dest = points[annotation.point_id]['annotations']['SEGMENT' if annotation.segment else 'POINT']
        content_type_name = models.ContentType.get_name(annotation.content_type)
        if not dest.has_key(content_type_name):
            dest[content_type_name] = []
        dest[content_type_name].append(annotation)

    points = sorted(points.values(), key=lambda p: p['order_rank'])

    segments = []
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        place_ids = '%s-%s' % (min(p1['place_id'], p2['place_id']), max(p1['place_id'], p2['place_id']))
        segments.append({'place_ids': place_ids, 'p1': p1, 'p2': p2, 'length': distance(p1['coords'], p2['coords']).km})

    trip_photos = [a for a in annotations if a.content_type == models.ContentType.EXTERNAL_PHOTOS]
    
    return views.render("trip_details.html", request, {'trip': trip, 'points': points, 'segments': segments,
                                                       'points_sorted': sorted(points, key=lambda p: p['place_id']), # XXX: needed until #11008 is fixed in Django
                                                       'segments_sorted': sorted(segments, key=lambda s: s['place_ids']), # XXX: needed until #11008 is fixed in Django
                                                       'trip_photos': trip_photos, 'show_trip_photos': trip.user == request.user or trip_photos})

def points_GET(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    points = list(trip.point_set.all())
    return views.render("trip_points.html", request, {'trip': trip, 'points': points})

points_re = re.compile(r"^(old|new)point_(.+)$")
def points_POST(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    points = list(trip.point_set.all())
    new_points = [dict([npi.split("=") for npi in np.split(",")])
                  for np in request.POST['points'].split(";") if np]

    for point in points:
        if not utils.find(new_points, lambda p: p['id'] == "oldpoint_%s" % point.id):
            point.delete()

    for i in range(len(new_points)):
        new_point = new_points[i]
        op, id = points_re.match(new_point['id']).groups()
        id = int(id)
        if op == 'old':
            point = utils.find(points, lambda p: p.id == id)
            modified = False
            if point.order_rank != i:
                point.order_rank = i
                modified = True
            if len(new_point) != 1: # this point was edited
                point.date_arrived = utils.parse_date(new_point['date_arrived'])
                point.date_left = utils.parse_date(new_point['date_left'])
                point.visited = bool(int(new_point['visited']))
                modified = True
            if modified:
                point.save()
        elif op == 'new':
            place_id = int(id)
            place = models.Place.objects.get(id=place_id)
            point = models.Point(trip=trip, place=place, name=place.name, coords=place.coords)
            point.date_arrived = utils.parse_date(new_point['date_arrived'])
            point.date_left = utils.parse_date(new_point['date_left'])
            point.visited = bool(int(new_point['visited']))
            point.order_rank = i
            point.save()
    return http.HttpResponse()

@login_required
@require_http_methods(["GET", "POST"])
def points(request, id):
    if request.method == 'GET':
        return points_GET(request, id)
    elif request.method == 'POST':
        return points_POST(request, id)

@login_required
@require_POST
def delete(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    trip.delete()
    return http.HttpResponse()

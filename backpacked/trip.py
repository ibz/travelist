import re

from geopy.distance import distance

from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.views.decorators.http import require_GET, require_POST, require_http_methods

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

def new_GET(request):
    trip = models.Trip(user=request.user)
    form = tripui.TripEditForm(instance=trip)
    return views.render("trip_new.html", request, {'trip': trip, 'trip_edit_form': form})

def new_POST(request):
    trip = models.Trip(user=request.user)
    form = tripui.TripEditForm(request.POST, instance=trip)
    if form.is_valid():
        trip = form.save()
        return http.HttpResponseRedirect("/trips/%s/" % trip.id)
    else:
        return http.HttpResponseBadRequest()

@login_required
@require_http_methods(["GET", "POST"])
def new(request):
    if request.method == 'GET':
        return new_GET(request)
    elif request.method == 'POST':
        return new_POST(request)

@require_GET
def view(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    if not trip.is_visible_to(request.user):
        raise http.Http404()
    form = tripui.TripEditForm(instance=trip)
    return views.render("trip.html", request, {'trip': trip, 'trip_edit_form': form})

@login_required
@require_POST
def edit(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    form = tripui.TripEditForm(request.POST, instance=trip)
    if form.is_valid():
        trip = form.save()
        return http.HttpResponse()
    else:
        return http.HttpResponseBadRequest()

@require_GET
def serialize(request, id, format):
    assert format == 'json'
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    if not trip.is_visible_to(request.user):
        raise http.Http404()
    data = {'id': trip.id,
            'name': trip.name,
            'start_date': utils.format_date(trip.start_date),
            'end_date': utils.format_date(trip.end_date),
            'visibility': trip.visibility}
    return http.HttpResponse(simplejson.dumps(data))

@require_GET
def details(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    if not trip.is_visible_to(request.user):
        raise http.Http404()

    sort_func = lambda lhs, rhs: cmp(lhs['order_rank'], rhs['order_rank'])

    annotations = trip.annotation_set.all()
    if trip.user != request.user:
        annotations = annotations.filter(visibility=models.Visibility.PUBLIC)
    annotations = list(annotations)

    points = {}
    for p in trip.point_set.all():
        points[p.id] = {'id': p.id,
                        'name': p.name, 'coords': p.coords.coords,
                        'date_arrived': p.date_arrived, 'date_left': p.date_left, 'visited': p.visited,
                        'order_rank': p.order_rank,
                        'annotations': []}
    for a in annotations:
        if not a.segment:
            points[a.point_id]['annotations'].append(a)
    points = sorted(points.values(), sort_func)

    segments = {}
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        segments[p1['id']] = {'id': p1['id'],
                              'p1_name' : p1['name'], 'p2_name': p2['name'],
                              'length': distance(p1['coords'], p2['coords']).km,
                              'order_rank': i,
                              'annotations': []}
    for a in annotations:
        if a.segment:
            segments[a.point_id]['annotations'].append(a)
    segments = sorted(segments.values(), sort_func)

    return views.render("trip_details.html", request, {'trip': trip, 'segments': segments, 'points': points})

def points_GET(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    points = sorted(list(trip.point_set.all()))
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
@require_GET
def delete(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    trip.delete()
    return http.HttpResponseRedirect("/trips/%s/" % request.user.username)

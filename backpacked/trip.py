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

@login_required
@require_GET
def all(request):
    trips = models.Trip.objects.filter(user=request.user).order_by('start_date')
    return views.render("trip_list.html", request, {'trips': trips})

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

def new_GET(request):
    trip = models.Trip(user=request.user)
    form = tripui.TripEditForm(instance=trip)
    return views.render("trip_new.html", request, {'trip': trip, 'trip_edit_form': form})

def new_POST(request):
    trip = models.Trip(user=request.user)
    form = tripui.TripEditForm(request.POST, instance=trip)
    if form.is_valid():
        trip = form.save()
        return http.HttpResponseRedirect("/trip/%s/" % trip.id)
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
    points = sorted(list(trip.point_set.all()))
    segments = []
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        length = distance(p1.coords.coords, p2.coords.coords).km
        annotations = p1.segment_annotations
        segment = {'p1': p1, 'p2': p2, 'length': length, 'annotations': annotations}
        segments.append(segment)
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
    return http.HttpResponseRedirect("/trip/all/")

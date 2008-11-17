import re

from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import forms
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
    form = forms.TripEditForm(instance=trip)
    return views.render("trip.html", request, {'trip': trip, 'trip_edit_form': form})

@login_required
@require_POST
def edit(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    form = forms.TripEditForm(request.POST, instance=trip)
    if form.is_valid():
        trip = form.save()
        return http.HttpResponse()
    else:
        return http.HttpResponseBadRequest()

def new_GET(request):
    trip = models.Trip(user=request.user)
    form = forms.TripEditForm(instance=trip)
    return views.render("trip_new.html", request, {'trip': trip, 'trip_edit_form': form})

def new_POST(request):
    trip = models.Trip(user=request.user)
    form = forms.TripEditForm(request.POST, instance=trip)
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
    segments = sorted(list(trip.segment_set.all()))
    points = []
    for segment in segments:
        for point in [segment.p1, segment.p2]:
            if not point in points:
                points.append(point)
    return views.render("trip_details.html", request, {'trip': trip, 'segments': segments, 'points': points})

def points_GET(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    assert len(list(trip.segment_set.all())) == 0
    assert len(list(trip.point_set.all())) == 0
    return views.render("trip_points.html", request, {'trip': trip})

def points_POST(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    assert len(list(trip.segment_set.all())) == 0
    assert len(list(trip.point_set.all())) == 0
    place_ids = [int(pid) for pid in request.POST['places'].split(",") if pid]
    points = []
    for place_id in place_ids:
        if not utils.find(points, lambda p: p.place_id == place_id):
            place = models.Place.objects.get(id=place_id)
            point = models.Point(trip=trip, place=place, name=place.name, coords=place.coords)
            point.save()
            points.append(point)
    for i in range(len(place_ids) - 1):
        place_id_1, place_id_2 = place_ids[i], place_ids[i + 1]
        p1 = utils.find(points, lambda p: p.place_id == place_ids[i])
        p2 = utils.find(points, lambda p: p.place_id == place_ids[i + 1])
        segment = models.Segment(trip=trip, p1=p1, p2=p2, order_rank=i)
        segment.save()
    return http.HttpResponse()

@login_required
@require_http_methods(["GET", "POST"])
def points(request, id):
    if request.method == 'GET':
        return points_GET(request, id)
    elif request.method == 'POST':
        return points_POST(request, id)

def segments_GET(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    segments = sorted(list(trip.segment_set.all()))
    return views.render("trip_segments.html", request, {'trip': trip, 'segments': segments})

def segments_POST(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id)
    segments = list(trip.segment_set.all())
    points = list(trip.point_set.all())
    new_segments = [dict([nsi.split("=") for nsi in ns.split(",")])
                    for ns in request.POST['segments'].split(";") if ns]

    # delete segments
    for segment in segments:
        if not utils.find(new_segments, lambda s: s['id'] == "oldsegment_%s" % segment.id):
            segment.delete()

    # add / modify segments
    for i in range(len(new_segments)):
        new_segment = new_segments[i]
        op, id = re.match(r"(old|new)segment_(.+)", new_segment['id']).groups()
        if op == 'old':
            segment = utils.find(segments, lambda s: s.id == int(id))
            segment.order_rank = i
            if len(new_segment) != 1: # this segment was edited
                segment.start_date = utils.parse_date(new_segment['start_date'])
                segment.end_date = utils.parse_date(new_segment['end_date'])
                segment.transportation_method = int(new_segment['transportation_method'])
            segment.save()
        elif op == 'new':
            p1_place_id, p2_place_id = [int(place_id) for place_id in id.split("x")]
            for place_id in [p1_place_id, p2_place_id]:
                if not utils.find(points, lambda p: p.place_id == place_id):
                    place = models.Place.objects.get(id=place_id)
                    point = models.Point(trip=trip, place=place, name=place.name, coords=place.coords)
                    point.save()
                    points.append(point)
            p1 = utils.find(points, lambda p: p.place_id == p1_place_id)
            p2 = utils.find(points, lambda p: p.place_id == p2_place_id)
            segment = models.Segment(trip=trip, p1=p1, p2=p2, order_rank=i)
            segment.start_date = utils.parse_date(new_segment['start_date'])
            segment.end_date = utils.parse_date(new_segment['end_date'])
            segment.transportation_method = int(new_segment['transportation_method'])
            segment.save()
            segments.append(segment)

    # delete useless points
    for point in list(trip.point_set.all()):
        if not utils.find(segments, lambda s: s.id and (s.p1_id == point.id or s.p2_id == point.id)):
            point.delete()
    return http.HttpResponse()

@login_required
@require_http_methods(["GET", "POST"])
def segments(request, id):
    if request.method == 'GET':
        return segments_GET(request, id)
    elif request.method == 'POST':
        return segments_POST(request, id)

@login_required
@require_GET
def delete(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    trip.delete()
    return http.HttpResponseRedirect("/trip/all/")

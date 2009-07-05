import re

from geopy.distance import distance

from django import forms
from django import http
from django import shortcuts
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.transaction import commit_on_success
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
        return http.HttpResponseRedirect(trip.get_absolute_url())
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
        return http.HttpResponseRedirect(trip.get_absolute_url())
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

    points = dict([(p.id, p) for p in trip.point_set.all()])
    for p in points.values():
        p.annotations = {'POINT': {}, 'SEGMENT': {}}

    annotations = list(trip.get_annotations_visible_to(request.user).all())
    for annotation in annotations:
        if not annotation.point_id:
            continue
        dest = points[annotation.point_id].annotations['SEGMENT' if annotation.segment else 'POINT']
        content_type_name = models.ContentType.get_name(annotation.content_type)
        if not dest.has_key(content_type_name):
            dest[content_type_name] = []
        dest[content_type_name].append(annotation)

    points = sorted(points.values(), key=lambda p: p.order_rank)

    segments = []
    for i in range(len(points) - 1):
        p1, p2 = points[i], points[i + 1]
        place_ids = '%s-%s' % (min(p1.place_id, p2.place_id), max(p1.place_id, p2.place_id))
        segments.append({'place_ids': place_ids, 'p1': p1, 'p2': p2, 'length': distance(p1.coords, p2.coords).km})

    trip_notes = [a for a in annotations if a.content_type in [models.ContentType.NOTE, models.ContentType.TWEET]]
    trip_photos = [a for a in annotations if a.content_type == models.ContentType.EXTERNAL_PHOTOS]
    trip_links = [(l.lhs if l.rhs == trip else l.rhs, l)
                  for l in models.TripLink.objects.filter(Q(lhs=trip) | Q(rhs=trip), status=models.RelationshipStatus.CONFIRMED)]
    trip_links = [l for l in trip_links if l[0].is_visible_to(request.user)]

    return views.render("trip_details.html", request, {'trip': trip, 'points': points, 'segments': segments,
                                                       'points_sorted': sorted(points, key=lambda p: p.place_id), # XXX: needed until #11008 is fixed in Django
                                                       'segments_sorted': sorted(segments, key=lambda s: s['place_ids']), # XXX: needed until #11008 is fixed in Django
                                                       'trip_notes': trip_notes, 'show_trip_notes': trip.user == request.user or trip_notes,
                                                       'trip_photos': trip_photos, 'show_trip_photos': trip.user == request.user or trip_photos,
                                                       'trip_links': trip_links, 'show_trip_links': trip.user == request.user or trip_links})

def points_GET(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    points = list(trip.point_set.all())
    widget = forms.widgets.Select(choices=annotationtypes.Transportation.Means.choices)
    return views.render("trip_points.html", request, {'trip': trip, 'points': points,
                                                      'transportation_select': widget.render('default_transportation', None, {'id': 'default_transportation'})})

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
            transportation = models.Annotation(trip=trip, point=point, segment=True, title="", content_type=models.ContentType.TRANSPORTATION)
            transportation.content = request.POST.get('default_transportation') or "0"
            transportation.save()
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

@commit_on_success
@login_required
@require_POST
def new_links(request, id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)

    assert trip.visibility == models.Visibility.PUBLIC

    users = models.User.objects.filter(id__in=[int(id) for id in set(request.POST['user_ids'].split(","))])
    friends = list(trip.user.get_friends())
    users = [u for u in users if utils.find(friends, lambda f: f == u)] # filter out non-friends
    notifications = list(models.Notification.objects.filter(user__in=users, type=models.NotificationType.TRIP_LINK_REQUEST))
    for r in trip.triplink_lhs_set.all(): # filter out already linked or invited
        if r.rhs:
            if r.rhs.user in users:
                users.remove(r.rhs.user)
        else:
            notification = utils.find(notifications, lambda n: int(n.content) == r.id)
            if notification:
                users.remove(notification.user)
    for r in trip.triplink_rhs_set.all(): # filter out already linked reverse
        if r.lhs.user in users:
            users.remove(r.lhs.user)

    if not users:
        return http.HttpResponse()

    for user in users:
        link = models.TripLink(lhs=trip, status=models.RelationshipStatus.PENDING)
        link.save()
        notification = models.Notification(user=user, type=models.NotificationType.TRIP_LINK_REQUEST)
        notification.content = str(link.id)
        notification.save()
        notification.manager.send_email()

    return http.HttpResponse()

@login_required
@require_POST
def delete_link(request, id, link_id):
    trip = shortcuts.get_object_or_404(models.Trip, id=id, user=request.user)
    link = models.TripLink.objects.get(Q(lhs=trip) | Q(rhs=trip), id=link_id)
    link.delete()

    return http.HttpResponse()

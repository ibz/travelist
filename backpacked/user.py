from geopy.distance import distance

from django import http
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.db.transaction import commit_on_success
from django.utils import html
from django.utils import safestring
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import annotationtypes
from backpacked import models
from backpacked import utils
from backpacked import views

@require_GET
def profile(request, username):
    profile = models.UserProfile.objects.filter(user__username=username).select_related('user').get()
    for_user = profile.user
    is_self, is_friend, is_friend_pending = for_user.get_relationship_status(request.user)
    return views.render("user_profile.html", request, {'for_user': for_user, 'is_self': is_self,
                                                       'is_friend': is_friend, 'is_friend_pending': is_friend_pending})

@login_required
@require_GET
def friends(request, username):
    return views.render("user_friends.html", request, {'for_user': models.User.objects.get(username=username)})

@commit_on_success
@login_required
@require_GET
def relationship(request, username):
    this_user = request.user
    other_user = models.User.objects.get(username=username)
    assert this_user != other_user
    try:
        this_user.get_relationship(other_user)
        assert False
    except models.UserRelationship.DoesNotExist:
        pass
    relationship = models.UserRelationship(lhs=this_user, rhs=other_user, status=models.RelationshipStatus.PENDING)
    relationship.save()
    notification = models.Notification(user=other_user, type=models.NotificationType.FRIEND_REQUEST, content=str(this_user.id))
    notification.save()
    notification.manager.send_email()
    return http.HttpResponseRedirect("/people/%s/" % other_user.username)

@require_GET
def map(request, username):
    user = models.User.objects.get(username=username)
    places = list(models.Place.objects.filter(point__trip__user=user, point__visited=True).annotate(visit_count=Count('point')).annotate(rating=Avg('placerating__value')))
    for place in places:
        place.rating = int(place.rating) if place.rating else models.Rating.AVERAGE
    return views.render("user_map.html", request, {'user': user, 'places': places})

@require_GET
def stats(request, username):
    user = models.User.objects.get(username=username)
    trips = list(user.trip_set.all())
    points = list(models.Point.objects.filter(trip__user=user).select_related('trip').select_related('place').select_related('place__country'))
    transportations = dict((t.point_id, int(t.content)) for t in models.Annotation.objects.filter(trip__user=user, content_type=models.ContentType.TRANSPORTATION))

    stats = {}

    def add_stat(year, stat, value, init):
        if not isinstance(year, int) and year is not None:
            for year in year:
                add_stat(year, stat, value, init)
        else:
            if not year in stats:
                stats[year] = {}
            if not stat in stats[year]:
                stats[year][stat] = init
            if isinstance(init, list):
                stats[year][stat].append(value)
            elif isinstance(init, set):
                stats[year][stat].add(value)
            else:
                stats[year][stat] += value
            if year is not None:
                add_stat(None, stat, value, init)

    for trip in trips:
        add_stat(range(trip.start_date.year, trip.end_date.year + 1), 'trip_count', 1, 0)

    for point in points:
        if point.visited:
            year_arrived = point.date_arrived.date().year if point.date_arrived else None
            add_stat(year_arrived, 'places', point.place, set())
            add_stat(year_arrived, 'countries', point.place.country, set())
        next_point = utils.find(points, lambda p: p.trip_id == point.trip_id and p.order_rank > point.order_rank)
        if next_point:
            dist = distance(point.coords, next_point.coords).km
            year_left = point.date_left.date().year if point.date_left else point.trip.start_date.year
            transportation = annotationtypes.Transportation.Means.get_name(transportations[point.id])
            add_stat(year_left, 'distance', dist, 0)
            add_stat(year_left, 'distance_' + transportation, dist, 0)

    for year_stats in stats.values():
        year_stats['places'] = sorted(year_stats.get('places', []))
        year_stats['countries'] = sorted(year_stats.get('countries', []))

    return views.render("user_stats.html", request, {'user': user,
                                                     'years': [None] + list(sorted(set(stats.keys()) - set([None]), reverse=True)),
                                                     'stats': stats.items()})

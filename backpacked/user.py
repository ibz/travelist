from django import http
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.db.transaction import commit_on_success
from django.utils import html
from django.utils import safestring
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models
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

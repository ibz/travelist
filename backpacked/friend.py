from django import http
from django.contrib.auth.decorators import login_required
from django.db.transaction import commit_on_success
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models
from backpacked import views

@login_required
@require_GET
def all(request):
    relationships = request.user.get_confirmed_relationships()
    friend_ids = [r.lhs_id != request.user.id and str(r.lhs_id) or str(r.rhs_id)
                  for r in relationships]
    if friend_ids:
        friends = models.UserProfile.objects.extra(where=["user_id IN (%s)" % ",".join(friend_ids)]).select_related('user')
    else:
        friends = []
    return views.render("friend_list.html", request, {'friends': friends})

@commit_on_success
@login_required
@require_GET
def add(request):
    username = request.GET.get('username')
    assert username
    user = models.User.objects.get(username=username)
    assert user != request.user
    try:
        request.user.get_relationship(user)
        assert False
    except models.UserRelationship.DoesNotExist:
        pass
    relationship = models.UserRelationship(lhs=request.user, rhs=user, status=models.RelationshipStatus.PENDING)
    relationship.save()
    notification = models.Notification(user=user, type=models.NotificationType.FRIEND_REQUEST, content=str(request.user.id))
    notification.save()
    return http.HttpResponseRedirect("/%s" % user.username)

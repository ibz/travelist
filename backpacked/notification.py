from django import http
from django import shortcuts
from django.contrib.auth.decorators import login_required
from django.db.transaction import commit_on_success
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models
from backpacked import views

@login_required
@require_GET
def all(request):
    notifications = models.Notification.objects.filter(user=request.user)
    return views.render("notification_list.html", request, {'notifications': notifications})

@commit_on_success
@login_required
@require_POST
def action(request, id):
    action_id = int(request.POST['action_id'])
    notification = shortcuts.get_object_or_404(models.Notification, id=id, user=request.user)
    notification.manager.action(action_id, request.POST)
    return http.HttpResponse()

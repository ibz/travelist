from django import http
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models
from backpacked import placeui
from backpacked import views

import settings

@require_GET
def search(request):
    def render(p):
        return "%s|%s|%s|%s,%s" % (p.display_name, p.id, p.name, p.coords.coords[0], p.coords.coords[1])
    places = models.Place.objects.filter(name_ascii__istartswith=request.GET['q'])[:15]
    return http.HttpResponse("\n".join([render(p) for p in places]))

@login_required
@require_POST
def suggest(request):
    suggestion = models.PlaceSuggestion(user=request.user)
    form = placeui.SuggestionForm(request.POST, instance=suggestion)
    if form.is_valid():
        suggestion = form.save()
        mail.mail_admins("New place suggestion",
                         "%s suggested %s" % (suggestion.user.username, suggestion.name))
        return http.HttpResponse()
    else:
        return http.HttpResponseBadRequest()


from django import http
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models
from backpacked import placeui
from backpacked import views

import settings

@require_GET
def search(request):
    def render(p):
        return "%s|%s|%s|%s,%s" % (p.display_name, p.id, p.name, p.coords.coords[0], p.coords.coords[1])
    query_terms = [t.strip() for t in request.GET['q'].split(",", 1)]
    places = models.Place.objects.filter(name_ascii__istartswith=query_terms[0])
    if len(query_terms) > 1:
        administrative_divisions = models.AdministrativeDivision.objects.filter(name__istartswith=query_terms[1])
        countries = models.Country.objects.filter(name__istartswith=query_terms[1])
        places = places.filter(Q(administrative_division__in=administrative_divisions) | Q(country__in=countries))
    places = places[:15]
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


from django import http
from django import shortcuts
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

@require_GET
def view(request, id):
    place = shortcuts.get_object_or_404(models.Place, id=id)

    if request.user.is_anonymous():
        user_ratings = []
    else:
        user_ratings = models.PlaceRating.objects.filter(place=place, user=request.user)
    user_rating = user_ratings[0] if len(user_ratings) == 1 else None

    return views.render("place.html", request, {'place': place, 'user_rating': user_rating})

def edit_GET(request, place):
    form = placeui.EditForm(instance=place)
    return views.render("place_edit.html", request, {'place': place, 'form': form})

def edit_POST(request, place):
    form = placeui.EditForm(request.POST, instance=place)
    if form.is_valid():
        form.save()
        hist = models.PlaceHist(place=place,
                                wiki_content=place.wiki_content,
                                user=request.user)
        hist.save()
        return http.HttpResponseRedirect("/places/%s/" % place.id)
    else:
        return views.render("place_edit.html", request, {'place': place, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, id):
    place = shortcuts.get_object_or_404(models.Place, id=id)
    if request.method == 'GET':
        return edit_GET(request, place)
    elif request.method == 'POST':
        return edit_POST(request, place)

@login_required
@require_GET
def rate(request, id):
    place = shortcuts.get_object_or_404(models.Place, id=id)

    models.PlaceRating.objects.filter(place=place, user=request.user).delete()

    rating = models.PlaceRating(place=place, user=request.user)
    rating.value = request.GET['value']
    rating.save()

    return http.HttpResponseRedirect("/places/%s/" % id)

@login_required
@require_POST
def comment(request, id):
    place = shortcuts.get_object_or_404(models.Place, id=id)

    comment = models.PlaceComment(place=place, user=request.user)
    comment.content = request.POST['comment_content']
    comment.save()

    return http.HttpResponseRedirect("/places/%s/" % id)

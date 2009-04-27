from django import http
from django import shortcuts
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import accommodationui
from backpacked import models
from backpacked import views

@require_GET
def view(request, id):
    accommodation = shortcuts.get_object_or_404(models.Accommodation, id=id)

    if request.user.is_anonymous():
        user_ratings = []
    else:
        user_ratings = models.AccommodationRating.objects.filter(accommodation=accommodation, user=request.user)
    user_rating = user_ratings[0] if len(user_ratings) == 1 else None

    return views.render("accommodation.html", request, {'accommodation': accommodation, 'user_rating': user_rating})

def edit_GET(request, accommodation):
    form = accommodationui.EditForm(instance=accommodation)
    return views.render("accommodation_edit.html", request, {'accommodation': accommodation, 'form': form})

def edit_POST(request, accommodation):
    form = accommodationui.EditForm(request.POST, instance=accommodation)
    if form.is_valid():
        form.save()
        hist = models.AccommodationHist(accommodation=accommodation,
                                        wiki_content=accommodation.wiki_content,
                                        user=request.user)
        hist.save()
        return http.HttpResponseRedirect("/accommodations/%s/" % accommodation.id)
    else:
        return views.render("accommodation_edit.html", request, {'accommodation': accommodation, 'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def edit(request, id):
    accommodation = shortcuts.get_object_or_404(models.Accommodation, id=id)
    if request.method == 'GET':
        return edit_GET(request, accommodation)
    elif request.method == 'POST':
        return edit_POST(request, accommodation)

@login_required
@require_GET
def rate(request, id):
    accommodation = shortcuts.get_object_or_404(models.Accommodation, id=id)

    models.AccommodationRating.objects.filter(accommodation=accommodation, user=request.user).delete()

    rating = models.AccommodationRating(accommodation=accommodation, user=request.user)
    rating.value = request.GET['value']
    rating.save()

    return http.HttpResponseRedirect("/accommodations/%s/" % id)

@login_required
@require_POST
def comment(request, id):
    accommodation = shortcuts.get_object_or_404(models.Accommodation, id=id)

    comment = models.AccommodationComment(accommodation=accommodation, user=request.user)
    comment.content = request.POST['comment_content']
    comment.save()

    return http.HttpResponseRedirect("/accommodations/%s/" % id)


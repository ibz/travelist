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
    return views.render("accommodation.html", request, {'accommodation': accommodation})

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

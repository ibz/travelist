from django import http
from django.contrib.auth.decorators import login_required
from django.core import mail
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models
from backpacked import suggestionui
from backpacked import views

def new_GET(request, suggestion):
    form = suggestionui.EditForm(instance=suggestion)
    return views.render("suggestion_new.html", request, {'form': form})

def new_POST(request, suggestion):
    form = suggestionui.EditForm(request.POST, instance=suggestion)
    if form.is_valid():
        suggestion = form.save()
        mail.mail_admins(models.SuggestionType.get_description(suggestion.type),
                         "%s said %s" % (suggestion.user.username, suggestion.comments))
        return http.HttpResponseRedirect("/")
    else:
        return views.render("suggestion_new.html", request, {'form': form})

@login_required
@require_http_methods(["GET", "POST"])
def new(request):
    suggestion = models.Suggestion(user=request.user)
    if request.method == 'GET':
        return new_GET(request, suggestion)
    else:
        return new_POST(request, suggestion)

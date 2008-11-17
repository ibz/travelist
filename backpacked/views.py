from django import http
from django import shortcuts
from django import template
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import forms
from backpacked import models
from backpacked import utils

import settings

def render(template_file, request, context=None):
    if not context:
        context = {}
    context['settings'] = settings
    context['visibility_choices'] = models.Visibility.choices
    context['transportation_method_choices'] = models.TransportationMethod.choices
    return shortcuts.render_to_response(template_file, context, context_instance=template.RequestContext(request))

@require_GET
def index(request):
    if request.user.is_authenticated():
        return http.HttpResponseRedirect("/trip/all/")
    else:
        return render("index.html", request, {'login_form': forms.AccountLoginForm()})

@require_GET
def place_search(request):
    def render(p):
        return "%s|%s|%s|%s,%s" % (p.display_name, p.id, p.name, p.coords.coords[0], p.coords.coords[1])
    places = models.Place.objects.filter(name_ascii__istartswith=request.GET['q'])[:15]
    return http.HttpResponse("\n".join([render(p) for p in places]))

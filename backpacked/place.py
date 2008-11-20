from django import http
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import models

@require_GET
def search(request):
    def render(p):
        return "%s|%s|%s|%s,%s" % (p.display_name, p.id, p.name, p.coords.coords[0], p.coords.coords[1])
    places = models.Place.objects.filter(name_ascii__istartswith=request.GET['q'])[:15]
    return http.HttpResponse("\n".join([render(p) for p in places]))

from django import http
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import views

available_sections = ['about', 'contact', 'twitter', 'flickr', 'faq']

@require_GET
def view(request, section):
    if section not in available_sections:
        return http.HttpResponseNotFound()
    return views.render("help_%s.html" % section, request)

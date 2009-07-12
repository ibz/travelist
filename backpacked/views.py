from django import http
from django import shortcuts
from django import template
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import accountui
from backpacked import models

import settings

_extra_context = None
def extra_context():
    global _extra_context
    if not _extra_context:
        from backpacked import annotationtypes
        _extra_context = {'settings': settings,
                          'TRANSPORTATION_CHOICES': annotationtypes.Transportation.Means.choices,
                          'RATINGS': dict((item, getattr(models.Rating, item)) for item in models.Rating.items)}
    return _extra_context

def render(template_file, request, context=None):
    if not context:
        context = {}
    context.update(extra_context())
    return shortcuts.render_to_response(template_file, context, context_instance=template.RequestContext(request))

@require_GET
def index(request):
    if request.user.is_authenticated():
        return http.HttpResponseRedirect("/trips/%s/" % request.user.username)
    else:
        return render("account_login.html", request, {'form': accountui.LoginForm()})

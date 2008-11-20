from django import http
from django import shortcuts
from django import template
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from backpacked import accountui
from backpacked import models

import settings

extra_context = {'settings': settings,
                 'content_type_choices': models.ContentType.choices,
                 'visibility_choices': models.Visibility.choices,
                 'transportation_method_choices': models.TransportationMethod.choices}

def render(template_file, request, context=None):
    if not context:
        context = {}
    context.update(extra_context)
    return shortcuts.render_to_response(template_file, context, context_instance=template.RequestContext(request))

@require_GET
def index(request):
    if request.user.is_authenticated():
        return http.HttpResponseRedirect("/trip/all/")
    else:
        return render("index.html", request, {'login_form': accountui.AccountLoginForm()})

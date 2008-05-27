from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^admin/', include('django.contrib.admin.urls')),

    (r"^/", 'web.views.index'),
    (r"^accounts/register/", 'web.views.register'),
    (r"^accounts/confirm/(?P<activation_key>\w+)", 'web.views.confirm')
)

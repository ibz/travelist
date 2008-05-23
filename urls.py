from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    # (r'^kashgar/', include('kashgar.foo.urls')),

    # Uncomment this for admin:
#     (r'^admin/', include('django.contrib.admin.urls')),

    (r"^/", 'web.views.index')
)

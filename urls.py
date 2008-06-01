from django.conf.urls.defaults import *

import settings

urlpatterns = patterns('',
    (r"^admin/",
      include('django.contrib.admin.urls')),
    (r'^media/(?P<path>.*)$',
      'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),
    (r"^$", 'web.views.index'),
    (r"^account/register/$",
      'web.views.account_register'),
    (r"^account/confirm/(?P<activation_key>\w+)/$",
      'web.views.account_confirm'),
    (r"^account/details/$",
      'web.views.account_details'),
    (r"^trip/list/$",
      'web.views.trip_list'),
    (r"^trip/((?P<id>\d+)/)?$",
      'web.views.trip_details'),
    (r"^location/$",
      'web.views.location'),
    (r"^point/(?P<point_id>\d+)/annotation/list/$",
      'web.views.annotation_list'),
    (r"^segment/(?P<segment_id>\d+)/annotation/list/$",
      'web.views.annotation_list')
)

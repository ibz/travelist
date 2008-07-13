from django.conf.urls.defaults import *

import settings

urlpatterns = patterns('',
    (r"^admin/",
      include('django.contrib.admin.urls')),
    (r'^media/(?P<path>.*)$',
      'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),

    (r"^$", 'backpacked.views.index'),

    (r"^account/register/$",
      'backpacked.views.account_register'),
    (r"^account/activate/(?P<activation_key>\w+)/$",
      'backpacked.views.account_activate'),
    (r"^account/details/$",
      'backpacked.views.account_details'),

    (r"^trip/list/$",
      'backpacked.views.trip_list'),
    (r"^trip/(?P<id>\d+)/$",
      'backpacked.views.trip_view'),
    (r"^trip/((?P<id>\d+)/)?edit/$",
      'backpacked.views.trip_edit'),

    (r"^place/search/$",
      'backpacked.views.place_search'),

    (r"^widget/segment_input/$",
      'backpacked.views.widget_segment_input'),

    (r"^point/(?P<point_id>\d+)/annotation/list/$",
      'backpacked.views.annotation_list'),
    (r"^segment/(?P<segment_id>\d+)/annotation/list/$",
      'backpacked.views.annotation_list')
)

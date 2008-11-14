from django.conf.urls.defaults import *
from django.contrib import admin

import settings

urlpatterns = patterns('',
    (r"^admin/", admin.site.root),
    (r'^media/(?P<path>.*)$',
      'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),

    (r"^$", 'backpacked.views.index'),

    (r"^account/login/$",
      'backpacked.views.account_login'),
    (r"^account/logout/$",
      'backpacked.views.account_logout'),
    (r"^account/register/$",
      'backpacked.views.account_register'),
    (r"^account/activate/(?P<activation_key>\w+)/$",
      'backpacked.views.account_activate'),
    (r"^account/details/$",
      'backpacked.views.account_details'),

    (r"^trip/list/$",
      'backpacked.views.trip_list'),
    (r"^trip/(?P<id>\d+)/((?P<format>json)/)?$",
      'backpacked.views.trip'),
    (r"^trip/new/$",
      'backpacked.views.trip_edit'),
    (r"^trip/(?P<id>\d+)/edit/$",
      'backpacked.views.trip_edit'),
    (r"^trip/(?P<id>\d+)/edit/create-segments/$",
      'backpacked.views.trip_create_segments'),
    (r"^trip/(?P<id>\d+)/edit/segments/$",
      'backpacked.views.trip_edit_segments'),
    (r"^trip/(?P<id>\d+)/delete/$",
      'backpacked.views.trip_delete'),

    (r"^place/search/$",
      'backpacked.views.place_search'),

    (r"^widget/content_input/$",
      'backpacked.views.widget_content_input'),

    (r"^trip/(?P<trip_id>\d+)/segment/(?P<id>\d+)/edit/$",
      'backpacked.views.segment_edit'),
    (r"^trip/(?P<trip_id>\d+)/(?P<entity>point|segment)/(?P<entity_id>\d+)/annotation/(?P<id>\d+)/$",
      'backpacked.views.annotation_view'),
    (r"^trip/(?P<trip_id>\d+)/(?P<entity>point|segment)/(?P<entity_id>\d+)/annotation/new/$",
      'backpacked.views.annotation_edit'),
    (r"^trip/(?P<trip_id>\d+)/(?P<entity>point|segment)/(?P<entity_id>\d+)/annotation/(?P<id>\d+)/edit/$",
      'backpacked.views.annotation_edit'),
    (r"^trip/(?P<trip_id>\d+)/(?P<entity>point|segment)/(?P<entity_id>\d+)/annotation/(?P<id>\d+)/delete/$",
      'backpacked.views.annotation_delete'),
)

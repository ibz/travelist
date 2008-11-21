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
      'backpacked.account.login'),
    (r"^account/logout/$",
      'backpacked.account.logout'),
    (r"^account/register/$",
      'backpacked.account.register'),
    (r"^account/confirm-email/(?P<username>\w+)/$",
      'backpacked.account.confirm_email'),
    (r"^account/details/$",
      'backpacked.account.details'),

    (r"^trip/all/$",
      'backpacked.trip.all'),
    (r"^trip/(?P<id>\d+)/$",
      'backpacked.trip.view'),
    (r"^trip/(?P<id>\d+)/edit/$",
      'backpacked.trip.edit'),
    (r"^trip/new/$",
      'backpacked.trip.new'),
    (r"^trip/(?P<id>\d+)/(?P<format>json)/$",
      'backpacked.trip.serialize'),
    (r"^trip/(?P<id>\d+)/details/$",
      'backpacked.trip.details'),
    (r"^trip/(?P<id>\d+)/points/$",
      'backpacked.trip.points'),
    (r"^trip/(?P<id>\d+)/segments/$",
      'backpacked.trip.segments'),
    (r"^trip/(?P<id>\d+)/delete/$",
      'backpacked.trip.delete'),

    (r"^place/search/$",
      'backpacked.place.search'),

    (r"^trip/(?P<trip_id>\d+)/annotation/all/$",
      'backpacked.annotation.all'),
    (r"^trip/(?P<trip_id>\d+)/annotation/(?P<id>\d+)/$",
      'backpacked.annotation.view'),
    (r"^trip/(?P<trip_id>\d+)/annotation/new/$",
     'backpacked.annotation.new'),
    (r"^trip/(?P<trip_id>\d+)/annotation/(?P<id>\d+)/edit/$",
      'backpacked.annotation.edit'),
    (r"^trip/(?P<trip_id>\d+)/annotation/(?P<id>\d+)/delete/$",
      'backpacked.annotation.delete'),
)

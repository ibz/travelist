from django.conf.urls.defaults import *
from django.contrib import admin

import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r"^_admin/(.*)$", admin.site.root),
    (r"^media/(?P<path>.*)$", 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),

    (r"^$", 'backpacked.views.index'),

    (r"^account/login/$", 'backpacked.account.login'),
    (r"^account/logout/$", 'backpacked.account.logout'),
    (r"^account/register/$", 'backpacked.account.register'),
    (r"^account/confirm-email/$", 'backpacked.account.confirm_email'),
    (r"^account/profile/$", 'backpacked.account.profile'),

    (r"^notifications/$", 'backpacked.notification.all'),
    (r"^notifications/(?P<id>\d+)/$", 'backpacked.notification.action'),

    (r"^people/(?P<username>\w+)/$", 'backpacked.user.profile'),
    (r"^people/(?P<username>\w+)/friends/$", 'backpacked.user.friends'),
    (r"^people/(?P<username>\w+)/relationship/$", 'backpacked.user.relationship'),

    (r"^places/search/$", 'backpacked.place.search'),

    (r"^trips/new/$", 'backpacked.trip.new'),
    (r"^trips/(?P<id>\d+)/$", 'backpacked.trip.view'),
    (r"^trips/(?P<id>\d+)/(?P<format>json)/$", 'backpacked.trip.serialize'),
    (r"^trips/(?P<id>\d+)/details/$", 'backpacked.trip.details'),
    (r"^trips/(?P<id>\d+)/points/$", 'backpacked.trip.points'),
    (r"^trips/(?P<id>\d+)/edit/$", 'backpacked.trip.edit'),
    (r"^trips/(?P<id>\d+)/delete/$", 'backpacked.trip.delete'),
    (r"^trips/(?P<username>\w+)/$", 'backpacked.trip.user'),

    (r"^trips/(?P<trip_id>\d+)/annotations/(?P<id>\d+)/$", 'backpacked.annotation.view'),
    (r"^trips/(?P<trip_id>\d+)/annotations/new/$", 'backpacked.annotation.new'),
    (r"^trips/(?P<trip_id>\d+)/annotations/(?P<id>\d+)/edit/$", 'backpacked.annotation.edit'),
    (r"^trips/(?P<trip_id>\d+)/annotations/(?P<id>\d+)/delete/$", 'backpacked.annotation.delete'),
)

from django.conf.urls.defaults import *
from django.contrib import admin

import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r"^_admin/(.*)$", admin.site.root),

    (r"^$", 'travelist.views.index'),

    (r"^account/login/$", 'travelist.account.login'),
    (r"^account/logout/$", 'travelist.account.logout'),
    (r"^account/register/$", 'travelist.account.register'),
    (r"^account/confirm-email/$", 'travelist.account.confirm_email'),
    (r"^account/profile/$", 'travelist.account.profile'),
    (r"^account/profile/connect/$", 'travelist.account.profile_connect'),

    (r"^help/(?P<section>\w+)/$", 'travelist.help.view'),

    (r"^suggestions/new/$", 'travelist.suggestion.new'),

    (r"^notifications/$", 'travelist.notification.all'),
    (r"^notifications/(?P<id>\d+)/$", 'travelist.notification.action'),

    (r"^people/(?P<username>\w+)/$", 'travelist.user.profile'),
    (r"^people/(?P<username>\w+)/friends/$", 'travelist.user.friends'),
    (r"^people/(?P<username>\w+)/relationship/$", 'travelist.user.relationship'),
    (r"^people/(?P<username>\w+)/map/$", 'travelist.user.map'),
    (r"^people/(?P<username>\w+)/stats/$", 'travelist.user.stats'),

    (r"^places/search/$", 'travelist.place.search'),
    (r"^places/suggest/$", 'travelist.place.suggest'),
    (r"^places/(?P<id>\d+)(-[\w-]+)?/$", 'travelist.place.view'),
    (r"^places/(?P<id>\d+)/edit/$", 'travelist.place.edit'),
    (r"^places/(?P<id>\d+)/rate/$", 'travelist.place.rate'),
    (r"^places/(?P<id>\d+)/comment/$", 'travelist.place.comment'),

    (r"^accommodations/(?P<id>\d+)(-[\w-]+)?/$", 'travelist.accommodation.view'),
    (r"^accommodations/(?P<id>\d+)/edit/$", 'travelist.accommodation.edit'),
    (r"^accommodations/(?P<id>\d+)/rate/$", 'travelist.accommodation.rate'),
    (r"^accommodations/(?P<id>\d+)/comment/$", 'travelist.accommodation.comment'),

    (r"^trips/new/$", 'travelist.trip.new'),
    (r"^trips/(?P<id>\d+)(-[\w-]+)?/$", 'travelist.trip.view'),
    (r"^trips/(?P<id>\d+)/details/$", 'travelist.trip.details'),
    (r"^trips/(?P<id>\d+)/points/$", 'travelist.trip.points'),
    (r"^trips/(?P<id>\d+)/edit/$", 'travelist.trip.edit'),
    (r"^trips/(?P<id>\d+)/delete/$", 'travelist.trip.delete'),
    (r"^trips/(?P<id>\d+)/journal/$", 'travelist.trip.journal'),

    (r"^trips/(?P<username>\w+)/$", 'travelist.trip.user'),

    (r"^trips/(?P<id>\d+)/links/new/$", 'travelist.trip.new_links'),
    (r"^trips/(?P<id>\d+)/links/(?P<link_id>\d+)/delete/$", 'travelist.trip.delete_link'),

    (r"^trips/(?P<trip_id>\d+)/annotations/(?P<id>\d+)/$", 'travelist.annotation.view'),
    (r"^trips/(?P<trip_id>\d+)/annotations/new/$", 'travelist.annotation.new'),
    (r"^trips/(?P<trip_id>\d+)/annotations/(?P<id>\d+)/edit/$", 'travelist.annotation.edit'),
    (r"^trips/(?P<trip_id>\d+)/annotations/(?P<id>\d+)/delete/$", 'travelist.annotation.delete'),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r"^media/(?P<path>.*)$", 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )

from django.contrib import admin
from django.core import mail

from backpacked import models
from backpacked import placeui

import settings

class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    ordering = ('name',)
    search_fields = ['name']
admin.site.register(models.Country, CountryAdmin)

class AdministrativeDivisionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'country')
    ordering = ('country__name', 'name')
    search_fields = ['name', 'country__name']
admin.site.register(models.AdministrativeDivision, AdministrativeDivisionAdmin)

class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'administrative_division', 'country', 'source_h', 'external_code')
    ordering = ('country__name', 'name')
    search_fields = ['name', 'administrative_division__name']
admin.site.register(models.Place, PlaceAdmin)

class PlaceNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'place')
    ordering = ('place__name', 'name')
    search_fields = ['name', 'place__name']
    raw_id_fields = ['place']
admin.site.register(models.PlaceName, PlaceNameAdmin)

class PlaceSuggestionAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'date')
    ordering = ('-date',)

    def __call__(self, request, url):
        if url and url.endswith("/resolved"):
            id = admin.util.unquote(url[:-len("/resolved")])
            suggestion = models.PlaceSuggestion.objects.get(id=id)
            mail.send_mail("Your place suggestion was accepted",
                           "The place %s was added to our database. You can use it in your own trips from now on." % request.POST.get('name'),
                           settings.SERVER_EMAIL,
                           [suggestion.user.email])
            return self.delete_view(request, id)
        else:
            return super(PlaceSuggestionAdmin, self).__call__(request, url)
admin.site.register(models.PlaceSuggestion, PlaceSuggestionAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'current_location', 'twitter_username', 'flickr_userid')
    ordering = ('user__username',)
    search_fields = ['user__username', 'user__email', 'name']
admin.site.register(models.UserProfile, UserProfileAdmin)

class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'comments')
    ordering = ('-date',)
admin.site.register(models.Suggestion, SuggestionAdmin)

class AccommodationAdmin(admin.ModelAdmin):
    list_display = ('name', 'place')
    ordering = ('name',)
admin.site.register(models.Accommodation, AccommodationAdmin)

class BackgroundTaskAdmin(admin.ModelAdmin):
    list_display = ('type_h', 'frequency_h', 'parameters', 'state')
admin.site.register(models.BackgroundTask, BackgroundTaskAdmin)

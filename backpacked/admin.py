from django.contrib import admin
from django.core import mail

from backpacked import models
from backpacked import placeui

import settings

class CountryAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
admin.site.register(models.Country, CountryAdmin)

class AdministrativeDivisionAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name', 'country__name']
admin.site.register(models.AdministrativeDivision, AdministrativeDivisionAdmin)

class PlaceAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name', 'administrative_division__name']
admin.site.register(models.Place, PlaceAdmin)

class PlaceSuggestionAdmin(admin.ModelAdmin):
    ordering = ['-date']

    def __call__(self, request, url):
        if url and url.endswith("/resolved"):
            id = admin.util.unquote(url[:-len("/resolved")])
            suggestion = models.PlaceSuggestion.objects.get(id=id)
            mail.send_mail("Your place suggestion was accepted",
                           "The place %s was added to our database. You can use it in your own trips from now on." % request.POST.get('name'),
                           settings.CUSTOMER_EMAIL,
                           [suggestion.user.email])
            return self.delete_view(request, id)
        else:
            return super(PlaceSuggestionAdmin, self).__call__(request, url)

admin.site.register(models.PlaceSuggestion, PlaceSuggestionAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    ordering = ['user__username']
    search_fields = ['user__username', 'user__email', 'name']
admin.site.register(models.UserProfile, UserProfileAdmin)

from django.contrib import admin

from backpacked import models

admin.site.register(models.Country)
admin.site.register(models.AdministrativeDivision)
admin.site.register(models.Place)
admin.site.register(models.UserProfile)

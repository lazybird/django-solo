from django.contrib import admin

from solo.admin import SingletonModelAdmin

from config.models import SiteConfiguration


admin.site.register(SiteConfiguration, SingletonModelAdmin)

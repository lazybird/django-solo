from django.contrib import admin

from config.models import SiteConfiguration
from solo.admin import SingletonModelAdmin

admin.site.register(SiteConfiguration, SingletonModelAdmin)

from django.db import models

from solo.models import SingletonModel


class SiteConfiguration(SingletonModel):
    site_name = models.CharField(max_length=255, default='Default Config')

    def __unicode__(self):
        return "Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"

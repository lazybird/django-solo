from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

from solo.models import SingletonModel


class SiteConfiguration(SingletonModel):
    site_name = models.CharField(max_length=255, default="Default Config")
    file = models.FileField(upload_to="files", default=SimpleUploadedFile("default-file.pdf", None))

    def __str__(self):
        return "Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"


class SiteConfigurationWithExplicitlyGivenId(SingletonModel):
    singleton_instance_id = 24
    site_name = models.CharField(max_length=255, default="Default Config")

    def __str__(self):
        return "Site Configuration"

    class Meta:
        verbose_name = "Site Configuration"

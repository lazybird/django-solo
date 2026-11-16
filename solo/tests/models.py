from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models
from django.utils import timezone

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


class ModelForRelations(models.Model):
    """
    For testing singleton models with relational fields.
    """


class SingletonWithRelationManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related("fk_relation")


class SingletonWithRelation(SingletonModel):
    # also covers one-to-one field as that's a subclass of foreignkey
    fk_relation = models.ForeignKey(ModelForRelations, on_delete=models.SET_NULL, null=True)
    datetime = models.DateTimeField(default=timezone.now)

    # m2m is not explicitly modelled, as the proper data model would just be a flat
    # table since singletons will only ever have one record in the through table

    objects = SingletonWithRelationManager()

    def __str__(self):
        return "Singleton with FK relation"

    class Meta:
        verbose_name = "Singleton with FK relation"

from django.core.cache import get_cache
from django.db import models

from solo import settings as solo_settings


class SingletonModel(models.Model):

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        self.set_to_cache()
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    def set_to_cache(self):
        if not solo_settings.SOLO_CACHE:
            return None
        cache = get_cache(solo_settings.SOLO_CACHE)
        cache_key = self.get_cache_key()
        cache.set(cache_key, self, solo_settings.SOLO_CACHE_TIMEOUT)

    @classmethod
    def get_cache_key(cls):
        prefix = solo_settings.SOLO_CACHE_PREFIX
        return '%s:%s' % (prefix, cls.__name__.lower())

    @classmethod
    def get_solo(cls):
        if not solo_settings.SOLO_CACHE:
            obj, creted = cls.objects.get_or_create(pk=1)
            return obj
        cache = get_cache(solo_settings.SOLO_CACHE)
        cache_key = cls.get_cache_key()
        obj = cache.get(cache_key)
        if not obj:
            obj, created = cls.objects.get_or_create(pk=1)
            obj.set_to_cache()
        return obj

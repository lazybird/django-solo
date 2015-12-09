from django.conf import settings
from django.db import models

try:
    from django.core.cache import caches
    get_cache = lambda cache_name: caches[cache_name]
except ImportError:
    from django.core.cache import get_cache

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
        cache_name = getattr(settings, 'SOLO_CACHE', solo_settings.SOLO_CACHE)
        if not cache_name:
            return None
        cache = get_cache(cache_name)
        cache_key = self.get_cache_key()
        timeout = getattr(settings, 'SOLO_CACHE_TIMEOUT', solo_settings.SOLO_CACHE_TIMEOUT)
        cache.set(cache_key, self, timeout)

    @classmethod
    def get_cache_key(cls):
        prefix = solo_settings.SOLO_CACHE_PREFIX
        return '%s:%s' % (prefix, cls.__name__.lower())

    @classmethod
    def get_solo(cls):
        cache_name = getattr(settings, 'SOLO_CACHE', solo_settings.SOLO_CACHE)
        if not cache_name:
            obj, created = cls.objects.get_or_create(pk=1)
            return obj
        cache = get_cache(cache_name)
        cache_key = cls.get_cache_key()
        obj = cache.get(cache_key)
        if not obj:
            obj, created = cls.objects.get_or_create(pk=1)
            obj.set_to_cache()
        return obj

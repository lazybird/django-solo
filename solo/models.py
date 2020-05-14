from django.conf import settings
from django.db import models

try:
    from django.core.cache import caches
    get_cache = lambda cache_name: caches[cache_name]
except ImportError:
    from django.core.cache import get_cache

from solo import settings as solo_settings

DEFAULT_SINGLETON_INSTANCE_ID = 1

class SingletonModel(models.Model):
    singleton_instance_id = DEFAULT_SINGLETON_INSTANCE_ID

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = self.singleton_instance_id
        super(SingletonModel, self).save(*args, **kwargs)
        self.set_to_cache()

    def delete(self, *args, **kwargs):
        self.clear_cache()
        super(SingletonModel, self).delete(*args, **kwargs)

    @classmethod
    def clear_cache(cls):
        cache_name = getattr(settings, 'SOLO_CACHE', solo_settings.SOLO_CACHE)
        if cache_name:
            cache = get_cache(cache_name)
            cache_key = cls.get_cache_key()
            cache.delete(cache_key)

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
        prefix = getattr(settings, 'SOLO_CACHE_PREFIX', solo_settings.SOLO_CACHE_PREFIX)
        return '%s:%s' % (prefix, cls.__name__.lower())

    @classmethod
    def get_solo(cls):
        cache_name = getattr(settings, 'SOLO_CACHE', solo_settings.SOLO_CACHE)
        if not cache_name:
            obj, created = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            return obj
        cache = get_cache(cache_name)
        cache_key = cls.get_cache_key()
        obj = cache.get(cache_key)
        if not obj:
            obj, created = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            obj.set_to_cache()
        return obj

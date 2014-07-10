from django.conf import settings
from django.core.cache import get_cache
from django.db import models

from solo import settings as solo_settings

class SingletonModelManager(models.Manager):
    def get_solo_pk(self):
        return 1

    def get_solo(self):
        return self.get_or_create(pk = self.get_solo_pk())

    def get(self, *args, **kwargs):
        return super(SingletonModelManager, self).get(id=self.get_solo_pk())

class SingletonModel(models.Model):
    objects = SingletonModelManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = self._default_manager.get_solo_pk()
        self.set_to_cache()
        super(SingletonModel, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise NotImplementedError('Deleting the Singleton settings entity is not implemented')

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
            obj, created = cls.objects.get_solo()
            return obj
        cache = get_cache(cache_name)
        cache_key = cls.get_cache_key()
        obj = cache.get(cache_key)
        if not obj:
            obj, created = cls.objects.get_solo()
            obj.set_to_cache()
        return obj



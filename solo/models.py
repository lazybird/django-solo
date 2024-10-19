from __future__ import annotations

import sys
import warnings
from typing import Any

from django.conf import settings
from django.core.cache import BaseCache, caches
from django.db import models

from solo import settings as solo_settings

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


DEFAULT_SINGLETON_INSTANCE_ID = 1


def get_cache(cache_name: str) -> BaseCache:
    warnings.warn(
        "'get_cache' is deprecated and will be removed in django-solo 2.4.0. "
        "Instead, use 'caches' from 'django.core.cache'.",
        DeprecationWarning,
        stacklevel=2,
    )
    return caches[cache_name]


class SingletonModel(models.Model):
    singleton_instance_id = DEFAULT_SINGLETON_INSTANCE_ID

    class Meta:
        abstract = True

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.pk = self.singleton_instance_id
        super().save(*args, **kwargs)
        self.set_to_cache()

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        self.clear_cache()
        return super().delete(*args, **kwargs)

    @classmethod
    def clear_cache(cls) -> None:
        cache_name = getattr(settings, "SOLO_CACHE", solo_settings.SOLO_CACHE)
        if cache_name:
            cache = caches[cache_name]
            cache_key = cls.get_cache_key()
            cache.delete(cache_key)

    def set_to_cache(self) -> None:
        cache_name = getattr(settings, "SOLO_CACHE", solo_settings.SOLO_CACHE)
        if not cache_name:
            return None
        cache = caches[cache_name]
        cache_key = self.get_cache_key()
        timeout = getattr(settings, "SOLO_CACHE_TIMEOUT", solo_settings.SOLO_CACHE_TIMEOUT)
        cache.set(cache_key, self, timeout)

    @classmethod
    def get_cache_key(cls) -> str:
        prefix = getattr(settings, "SOLO_CACHE_PREFIX", solo_settings.SOLO_CACHE_PREFIX)
        # Include the model's module in the cache key so similarly named models from different
        # apps do not have the same cache key.
        return f"{prefix}:{cls.__module__.lower()}:{cls.__name__.lower()}"

    @classmethod
    def get_solo(cls) -> Self:
        cache_name = getattr(settings, "SOLO_CACHE", solo_settings.SOLO_CACHE)
        if not cache_name:
            obj, _ = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            return obj
        cache = caches[cache_name]
        cache_key = cls.get_cache_key()
        obj = cache.get(cache_key)
        if not obj:
            obj, _ = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            obj.set_to_cache()
        return obj

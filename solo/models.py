from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core import serializers
from django.core.cache import caches
from django.db import models
from django.db.models.fields.mixins import FieldCacheMixin

from solo import settings as solo_settings

DEFAULT_SINGLETON_INSTANCE_ID = 1

_CACHE_VERSION = 2
"""
Version of the internal cache data format.

Increment this when modifying the cache data (de)serialization logic.
"""


def prepare_for_cache(instance: models.Model) -> Mapping[str, object]:
    """
    Prepare model instance data for the cache.

    The return value must consist of types that can be JSON-encoded to support
    cache backends that don't rely on pickle. Cache backends are responsible for
    using an appropriate serializer class, e.g.
    :class:`django.core.serializers.json.DjangoJSONEncoder`
    """
    data = serializers.serialize("python", [instance])[0]

    opts = instance._meta
    related: dict[str, Mapping[str, object]] = {}
    for field in opts.concrete_fields:
        # don't hit the DB when serializing related fields along
        if (
            not field.is_relation
            or not isinstance(field, FieldCacheMixin)
            or not field.is_cached(instance)
        ):
            continue
        related_value = field.get_cached_value(instance)
        assert related_value is not None
        related[field.name] = prepare_for_cache(related_value)

    return {"object": data, "related": related}


def recreate_from_cache(data: Mapping[str, object]) -> models.Model:
    # deserialize the top-level object first and then figure out the related fields
    instance = next(serializers.deserialize("python", [data["object"]])).object
    instance._state.adding = False

    # and recursively re-populate the related fields
    assert isinstance(data["related"], Mapping)
    for name, related_data in data["related"].items():
        related_object = recreate_from_cache(related_data)
        setattr(instance, name, related_object)

    return instance


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
            cache.delete(cache_key, version=_CACHE_VERSION)

    def set_to_cache(self) -> None:
        cache_name = getattr(settings, "SOLO_CACHE", solo_settings.SOLO_CACHE)
        if not cache_name:
            return None
        cache = caches[cache_name]
        cache_key = self.get_cache_key()
        timeout = getattr(settings, "SOLO_CACHE_TIMEOUT", solo_settings.SOLO_CACHE_TIMEOUT)
        cache_value = prepare_for_cache(self)
        cache.set(cache_key, cache_value, timeout, version=_CACHE_VERSION)

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
        model_data = cache.get(cache_key, default=None, version=_CACHE_VERSION)
        if model_data is None:
            obj, _ = cls.objects.get_or_create(pk=cls.singleton_instance_id)
            obj.set_to_cache()
        else:
            instance = recreate_from_cache(model_data)
            assert isinstance(instance, cls)
            obj = instance
        return obj

    @classmethod
    async def aget_solo(cls) -> Self:
        return await sync_to_async(cls.get_solo)()

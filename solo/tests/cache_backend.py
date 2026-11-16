import json

from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.core.cache.backends.locmem import LocMemCache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


class CustomCache(LocMemCache):
    """
    Custom cache backend that uses JSON serialization for non-model instances.

    Created for issue #102 to ensure that cache backends without pickle can be
    supported.
    """

    def get(self, key, default=None, version=None):
        value = super().get(key, default=default, version=version)
        if value == default:
            return value
        # non-model instances are expected to have been json serialized
        if not isinstance(value, models.Model):
            value = json.loads(value)
        return value

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None):
        # json-serialize non-solo instances. Model instances themselves are passed
        # through as is.
        if not isinstance(value, models.Model):
            value = json.dumps(value, cls=DjangoJSONEncoder)
        return super().set(key, value, timeout=timeout, version=version)

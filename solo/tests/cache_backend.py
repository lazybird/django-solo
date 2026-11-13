from django.core.cache.backends.locmem import LocMemCache


class CustomCache(LocMemCache):
    """
    Custom cache backend that uses JSON serialization for non-model instances.

    Created for issue #102 to ensure that cache backends without pickle can be
    supported.
    """

from django.conf import settings

GET_SOLO_TEMPLATE_TAG_NAME = getattr(settings,
    'GET_SOLO_TEMPLATE_TAG_NAME', 'get_solo')

# The cache that should be used, e.g. 'default'. Refers to Django CACHES setting.
# Set to None to disable caching.
SOLO_CACHE = None

SOLO_CACHE_TIMEOUT = 60*5

SOLO_CACHE_PREFIX = 'solo'

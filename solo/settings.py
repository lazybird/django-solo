from django.conf import settings

# template parameters
GET_SOLO_TEMPLATE_TAG_NAME = getattr(settings,
    'GET_SOLO_TEMPLATE_TAG_NAME', 'get_solo')

SOLO_ADMIN_SKIP_OBJECT_LIST_PAGE = getattr(settings,
    'SOLO_ADMIN_SKIP_OBJECT_LIST_PAGE', True)

# The cache that should be used, e.g. 'default'. Refers to Django CACHES setting.
# Set to None to disable caching.
SOLO_CACHE = None

SOLO_CACHE_TIMEOUT = 60*5

SOLO_CACHE_PREFIX = 'solo'
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'solo-tests.db',
    }
}

INSTALLED_APPS = (
    'solo',
    'solo.tests',
)

SECRET_KEY = 'any-key'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': '127.0.0.1:11211',
    },
}

SOLO_CACHE = 'default'

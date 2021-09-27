"""django-solo helps working with singletons: things like global settings that you want to edit from the admin site.
"""
import django


__version__ = '1.2.0'
__doc__ = 'Django Solo helps working with singletons'

if django.VERSION < (3, 2):
    default_app_config = 'solo.apps.SoloAppConfig'

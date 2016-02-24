
Django Solo
===========


    +---------------------------+
    |                           |
    |                           |
    |             \             | Django Solo helps working with singletons:
    |             /\            | database tables that only have one row.
    |           >=)'>           | Singletons are useful for things like global
    |             \/            | settings that you want to edit from the admin
    |             /             | instead of having them in Django settings.py.
    |                           | 
    |                           | 
    +---------------------------+


Features
--------

Solo helps you enforce instantiating only one instance of a model in django.

* You define the model that will hold your singleton object.
* django-solo gives helper parent class for your model and the admin classes.
* You get an admin interface that's aware you only have one object.
* You can retrieve the object from templates.
* By enabling caching, the database is not queried intensively.

Use Cases
--------

Django Solo is also great for use with singleton objects that have a one to many relationship. Like the use case below where you have a 'Home Slider" that has many "Slides".

* Global or default settings
* An image slider that has many slides
* A page section that has sub-sections
* A team bio with many team members

There are many cases where it makes sense for the parent in a one to many relationship to be limited to a single instance.

Usage Example
-------------

    # models.py

    from django.db import models
    from solo.models import SingletonModel

    class SiteConfiguration(SingletonModel):
        site_name = models.CharField(max_length=255, default='Site Name')
        maintenance_mode = models.BooleanField(default=False)

        def __unicode__(self):
            return u"Site Configuration"

        class Meta:
            verbose_name = "Site Configuration"

    # admin.py

    from django.contrib import admin
    from solo.admin import SingletonModelAdmin
    from config.models import SiteConfiguration

    admin.site.register(SiteConfiguration, SingletonModelAdmin)

    # There is only one item in the table, you can get it this way:
    from .models import SiteConfiguration
    config = SiteConfiguration.objects.get()

    # get_solo will create the item if it does not already exist
    config = SiteConfiguration.get_solo()


In your model, note how you did not have to provide a `verbose_name_plural` field -
That's because Django Solo uses the `verbose_name` instead.

If you're changing an existing model (which already has some objects stored in the database) to a singleton model, you can explicitly provide the id of the row in the database to use by django-solo as singleton. This can be done by setting `singleton_instance_id` property on the model`:

    class SiteConfiguration(SingletonModel):
        singleton_instance_id = 24
        # (...)

Installation
------------

This application requires Django >= 1.6.

* Install the package using `pip install django-solo`
* Add ``solo`` or ``solo.apps.SoloAppConfig`` to your ``INSTALLED_APPS`` setting.

This is how you run tests:

    ./manage.py test solo --settings=solo.tests.settings


Admin
-----

The standard Django admin does not fit well when working with singleton,
for instance, if you need some global site settings to be edited in the admin.
Django Solo provides a modified admin for that.


![django-solo admin](https://raw.github.com/lazybird/django-solo/master/docs/images/django-solo-admin.jpg "django-solo admin")


* In the admin home page where all applications are listed, we have a `config`
  application that holds a singleton model for site configuration.
* The configuration object can only be changed, there's no link for "add" (1).
* The link to the configuration page (2) directly goes to the form page - no
  need for an intermediary object list page, since there's only one object.
* The edit page has a modified breadcrumb (3) to avoid linking to the
  intermediary object list page.
* From the edit page, we cannot delete the object (4) nor can we add a new one (5).


Availability from templates
---------------------------

The singleton object can be retrieved from template by giving the Django model
dotted path:

    {% get_solo 'app_label.ModelName' as my_config %}


Example:


    {% load solo_tags %}
    {% get_solo 'config.SiteConfiguration' as site_config %}
    {{ site_config.site_name }}
    {{ site_config.maintenance_mode }}


Caching
-------

By default caching is disabled: every time `get_solo` retrieves the singleton
object, there will be a database query.

You can enable caching to only query the database when initially retrieving the
object. The cache will also be updated when updates are made from the admin.

The cache timeout is controlled via the `SOLO_CACHE_TIMEOUT` settings.
The cache backend to be used is controlled via the `SOLO_CACHE` settings.


Settings
--------

### Template Tag Name

You can retrieve your singleton object in templates using the `get_solo`
template tag.

You can change the name `get_solo` using the
`GET_SOLO_TEMPLATE_TAG_NAME` setting.

    GET_SOLO_TEMPLATE_TAG_NAME = 'get_config'

### Cache backend

Django provides a way to define multiple cache backends with the `CACHES`
settings. If you want the singleton object to be cached separately, you
could define the `CACHES` and the `SOLO_CACHE` settings like this:

    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        },
        'local': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        },
    }

    SOLO_CACHE = 'local'


Caching will be disabled if set to `None`.


### Cache timeout

The cache timeout in seconds.

    SOLO_CACHE_TIMEOUT = 60*5  # 5 mins

### Cache prefix

The prefix to use for the cache key.

    SOLO_CACHE_PREFIX = 'solo'

================
Getting the code
================

The code is hosted at https://github.com/lazybird/django-solo/

Check out the latest development version anonymously with::

    $ git clone git://github.com/lazybird/django-solo.git

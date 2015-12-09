from django.template import Template, Context
from django.test import TestCase

from django.test.utils import override_settings
from solo.models import get_cache
from solo.tests.models import SiteConfiguration


class SigletonTest(TestCase):

    def setUp(self):
        self.template = Template(
            '{% load solo_tags %}'
            '{% get_solo "tests.SiteConfiguration" as site_config  %}'
            '{{ site_config.site_name }}'
        )
        self.cache = get_cache('default')
        self.cache_key = SiteConfiguration.get_cache_key()
        self.cache.clear()
        SiteConfiguration.objects.all().delete()

    def test_template_tag_renders_default_site_config(self):
        SiteConfiguration.objects.all().delete()
        # At this point, there is no configuration object and we expect a
        # one to be created automatically with the default name value as
        # defined in models.
        output = self.template.render(Context())
        self.assertIn('Default Config', output)

    def test_template_tag_renders_site_config(self):
        SiteConfiguration.objects.create(site_name='Test Config')
        output = self.template.render(Context())
        self.assertIn('Test Config', output)

    @override_settings(SOLO_CACHE='default')
    def test_template_tag_uses_cache_if_enabled(self):
        SiteConfiguration.objects.create(site_name='Config In Database')
        fake_configuration = {'site_name': 'Config In Cache'}
        self.cache.set(self.cache_key, fake_configuration, 10)
        output = self.template.render(Context())
        self.assertNotIn('Config In Database', output)
        self.assertNotIn('Default Config', output)
        self.assertIn('Config In Cache', output)

    @override_settings(SOLO_CACHE=None)
    def test_template_tag_uses_database_if_cache_disabled(self):
        SiteConfiguration.objects.create(site_name='Config In Database')
        fake_configuration = {'site_name': 'Config In Cache'}
        self.cache.set(self.cache_key, fake_configuration, 10)
        output = self.template.render(Context())
        self.assertNotIn('Config In Cache', output)
        self.assertNotIn('Default Config', output)
        self.assertIn('Config In Database', output)

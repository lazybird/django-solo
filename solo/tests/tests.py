from unittest.mock import patch

from django.conf import settings
from django.contrib.admin import AdminSite
from django.core.cache import caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template, TemplateSyntaxError
from django.test import RequestFactory, SimpleTestCase, TestCase
from django.test.utils import override_settings
from django.utils.html import format_html
from django.utils.translation import gettext, override

from solo.admin import SingletonModelAdmin
from solo.tests.models import SiteConfiguration, SiteConfigurationWithExplicitlyGivenId
from solo.tests.testapp2.models import SiteConfiguration as SiteConfiguration2


class SingletonTest(TestCase):
    def setUp(self):
        self.template = Template(
            "{% load solo_tags %}"
            '{% get_solo "tests.SiteConfiguration" as site_config  %}'
            "{{ site_config.site_name }}"
            "{{ site_config.file.url }}"
        )
        self.template_invalid_app = Template(
            "{% load solo_tags %}"
            '{% get_solo "invalid_app.SiteConfiguration" as site_config  %}'
            "{{ site_config.site_name }}"
            "{{ site_config.file.url }}"
        )
        self.template_invalid_model = Template(
            "{% load solo_tags %}"
            '{% get_solo "tests.InvalidModel" as site_config  %}'
            "{{ site_config.site_name }}"
            "{{ site_config.file.url }}"
        )
        self.cache = caches["default"]
        self.cache_key = SiteConfiguration.get_cache_key()
        self.cache.clear()
        SiteConfiguration.objects.all().delete()

    def test_template_tag_renders_default_site_config(self):
        SiteConfiguration.objects.all().delete()
        # At this point, there is no configuration object and we expect a
        # one to be created automatically with the default name value as
        # defined in models.
        output = self.template.render(Context())
        self.assertIn("Default Config", output)

    def test_template_tag_renders_site_config(self):
        SiteConfiguration.objects.create(site_name="Test Config")
        output = self.template.render(Context())
        self.assertIn("Test Config", output)

    @override_settings(SOLO_CACHE="default")
    def test_template_tag_uses_cache_if_enabled(self):
        SiteConfiguration.objects.create(site_name="Config In Database")
        fake_configuration = {"site_name": "Config In Cache"}
        self.cache.set(self.cache_key, fake_configuration, 10)
        output = self.template.render(Context())
        self.assertNotIn("Config In Database", output)
        self.assertNotIn("Default Config", output)
        self.assertIn("Config In Cache", output)

    @override_settings(SOLO_CACHE=None)
    def test_template_tag_uses_database_if_cache_disabled(self):
        SiteConfiguration.objects.create(site_name="Config In Database")
        fake_configuration = {"site_name": "Config In Cache"}
        self.cache.set(self.cache_key, fake_configuration, 10)
        output = self.template.render(Context())
        self.assertNotIn("Config In Cache", output)
        self.assertNotIn("Default Config", output)
        self.assertIn("Config In Database", output)

    @override_settings(SOLO_CACHE="default")
    def test_delete_if_cache_enabled(self):
        self.assertEqual(SiteConfiguration.objects.count(), 0)
        self.assertIsNone(self.cache.get(self.cache_key))

        one_cfg = SiteConfiguration.get_solo()
        one_cfg.site_name = "TEST SITE PLEASE IGNORE"
        one_cfg.save()
        self.assertEqual(SiteConfiguration.objects.count(), 1)
        self.assertIsNotNone(self.cache.get(self.cache_key))

        one_cfg.delete()
        self.assertEqual(SiteConfiguration.objects.count(), 0)
        self.assertIsNone(self.cache.get(self.cache_key))
        self.assertEqual(SiteConfiguration.get_solo().site_name, "Default Config")

    @override_settings(SOLO_CACHE=None)
    def test_delete_if_cache_disabled(self):
        # As above, but without the cache checks
        self.assertEqual(SiteConfiguration.objects.count(), 0)
        one_cfg = SiteConfiguration.get_solo()
        one_cfg.site_name = "TEST (uncached) SITE PLEASE IGNORE"
        one_cfg.save()
        self.assertEqual(SiteConfiguration.objects.count(), 1)
        one_cfg.delete()
        self.assertEqual(SiteConfiguration.objects.count(), 0)
        self.assertEqual(SiteConfiguration.get_solo().site_name, "Default Config")

    @override_settings(SOLO_CACHE="default")
    def test_file_upload_if_cache_enabled(self):
        cfg = SiteConfiguration.objects.create(
            site_name="Test Config", file=SimpleUploadedFile("file.pdf", None)
        )
        output = self.template.render(Context())
        self.assertIn(cfg.file.url, output)

    @override_settings(SOLO_CACHE_PREFIX="other")
    def test_cache_prefix_overriding(self):
        key = SiteConfiguration.get_cache_key()
        prefix = key.partition(":")[0]
        self.assertEqual(prefix, "other")

    def test_template_tag_invalid_app_name(self):
        with self.assertRaises(TemplateSyntaxError):
            self.template_invalid_app.render(Context())

    def test_template_invalid_model_name(self):
        with self.assertRaises(TemplateSyntaxError):
            self.template_invalid_model.render(Context())


class SingletonWithExplicitIdTest(TestCase):
    def setUp(self):
        SiteConfigurationWithExplicitlyGivenId.objects.all().delete()

    def test_when_singleton_instance_id_is_given_created_item_will_have_given_instance_id(self):
        item = SiteConfigurationWithExplicitlyGivenId.get_solo()
        self.assertEqual(item.pk, SiteConfigurationWithExplicitlyGivenId.singleton_instance_id)


class SingletonsWithAmbiguousNameTest(TestCase):
    def test_cache_key_is_not_ambiguous(self):
        assert SiteConfiguration.get_cache_key() != SiteConfiguration2.get_cache_key()

    def test_get_solo_returns_the_correct_singleton(self):
        assert SiteConfiguration.get_solo() != SiteConfiguration2.get_solo()


@override_settings(
    INSTALLED_APPS=[
        *settings.INSTALLED_APPS,
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
    ],
    USE_I18N=True,
)
class SingletonAdminTranslationTest(SimpleTestCase):
    def test_change_messages_use_django_admin_translations(self):
        model_admin = SingletonModelAdmin(SiteConfiguration, AdminSite())
        obj = SiteConfiguration(site_name="<script>unsafe</script>")
        for language in ("en", "nb", "es", "de"):
            for continue_editing in (False, True):
                with self.subTest(language=language, continue_editing=continue_editing):
                    data = {"_continue": "1"} if continue_editing else {}
                    request = RequestFactory().post("/admin/config/", data)
                    message = (
                        "The {name} “{obj}” was changed successfully. You may edit it again below."
                        if continue_editing
                        else "The {name} “{obj}” was changed successfully."
                    )
                    with (
                        override(language),
                        patch.object(model_admin, "message_user") as notify,
                        patch.object(
                            SiteConfiguration, "__str__", return_value="<script>unsafe</script>"
                        ),
                    ):
                        translated = gettext(message)
                        if language != "en":
                            self.assertNotEqual(translated, message)
                        response = model_admin.response_change(request, obj)
                        expected = format_html(
                            translated, name=obj._meta.verbose_name, obj=str(obj)
                        )
                    self.assertEqual(notify.call_args.args[1], expected)
                    self.assertNotIn("<script>", notify.call_args.args[1])
                    self.assertEqual(response.url, request.path if continue_editing else "../../")

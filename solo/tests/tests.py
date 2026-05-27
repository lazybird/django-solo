from django.core.cache import caches
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.template import Context, Template, TemplateSyntaxError
from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings

from solo.tests.models import SiteConfiguration, SiteConfigurationWithExplicitlyGivenId
from solo.tests.testapp2.models import SiteConfiguration as SiteConfiguration2


class _RollbackError(Exception):
    """Raised inside ``atomic()`` to force a rollback in the tests below."""


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
        # save() now updates the cache via transaction.on_commit, which does not
        # fire inside the transaction TestCase wraps each test in, so capture and
        # execute the on_commit callbacks to observe the cache update.
        with self.captureOnCommitCallbacks(execute=True):
            one_cfg.save()
        self.assertEqual(SiteConfiguration.objects.count(), 1)
        self.assertIsNotNone(self.cache.get(self.cache_key))

        with self.captureOnCommitCallbacks(execute=True):
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


@override_settings(SOLO_CACHE="default")
class TransactionRollbackCacheTest(TransactionTestCase):
    """Regression tests: a rollback of an outer transaction must not poison the cache.

    These rely on ``transaction.on_commit`` callbacks actually firing on commit and
    being discarded on rollback, so they use ``TransactionTestCase``. A plain
    ``TestCase`` wraps every test in a transaction that never commits, which would
    suppress the ``on_commit`` callbacks and make the ``save``/``delete`` fixes
    look broken. The cache must be enabled (``SOLO_CACHE`` set) for any of this to
    matter, as ``set_to_cache``/``clear_cache`` are no-ops otherwise.
    """

    def setUp(self):
        self.cache = caches["default"]
        self.cache_key = SiteConfiguration.get_cache_key()
        # LocMemCache is process-global and not reset between tests.
        self.cache.clear()
        SiteConfiguration.objects.all().delete()

    def test_save_in_rolled_back_transaction_does_not_poison_cache(self):
        # Establish a committed value, present in both the DB and the cache.
        cfg = SiteConfiguration.get_solo()
        cfg.site_name = "Committed"
        cfg.save()
        self.assertEqual(self.cache.get(self.cache_key).site_name, "Committed")

        # Save a new value inside a transaction that rolls back.
        with self.assertRaises(_RollbackError), transaction.atomic():
            cfg.site_name = "Rolled back"
            cfg.save()
            raise _RollbackError

        # The DB reverted to the committed value...
        self.assertEqual(SiteConfiguration.objects.get(pk=cfg.pk).site_name, "Committed")
        # ...and the cache must not hold the rolled-back value.
        self.assertEqual(self.cache.get(self.cache_key).site_name, "Committed")

    def test_delete_in_rolled_back_transaction_does_not_poison_cache(self):
        # Establish a committed value, present in both the DB and the cache.
        cfg = SiteConfiguration.get_solo()
        cfg.site_name = "Committed"
        cfg.save()
        self.assertEqual(self.cache.get(self.cache_key).site_name, "Committed")

        # Delete inside a transaction that rolls back. Capture the pk first, as
        # Model.delete() resets the in-memory instance's pk to None.
        pk = cfg.pk
        with self.assertRaises(_RollbackError), transaction.atomic():
            cfg.delete()
            raise _RollbackError

        # The row still exists (the delete was rolled back)...
        self.assertEqual(SiteConfiguration.objects.filter(pk=pk).count(), 1)
        # ...and the cache must still hold the (not-actually-deleted) value.
        cached = self.cache.get(self.cache_key)
        self.assertIsNotNone(cached)
        self.assertEqual(cached.site_name, "Committed")

    def test_get_solo_create_on_miss_in_rolled_back_transaction_does_not_poison_cache(self):
        # Start with no row and an empty cache.
        self.assertEqual(SiteConfiguration.objects.count(), 0)
        self.assertIsNone(self.cache.get(self.cache_key))

        # A cache-miss read inside a transaction creates the row, then rolls back.
        with self.assertRaises(_RollbackError), transaction.atomic():
            obj = SiteConfiguration.get_solo()
            self.assertEqual(obj.site_name, "Default Config")
            raise _RollbackError

        # The created row was rolled back...
        self.assertEqual(SiteConfiguration.objects.count(), 0)
        # ...and the cache must not hold an object for the row that no longer exists.
        self.assertIsNone(self.cache.get(self.cache_key))

    def test_get_solo_caching_uncommitted_read_in_rolled_back_transaction_does_not_poison_cache(
        self,
    ):
        # Commit an initial value, then drop it from the cache so the next read
        # is a cache miss that goes to the DB (as if SOLO_CACHE_TIMEOUT expired).
        cfg = SiteConfiguration.get_solo()
        cfg.site_name = "Committed"
        cfg.save()
        self.cache.clear()

        # Inside a transaction: modify the row, then a cache-miss read repopulates
        # the cache from the (uncommitted) DB state. The transaction then rolls back.
        with self.assertRaises(_RollbackError), transaction.atomic():
            cfg.site_name = "Rolled back"
            cfg.save()
            reread = SiteConfiguration.get_solo()
            self.assertEqual(reread.site_name, "Rolled back")
            raise _RollbackError

        # The DB reverted to the committed value...
        self.assertEqual(SiteConfiguration.objects.get(pk=cfg.pk).site_name, "Committed")
        # ...and the cache must not hold the rolled-back value.
        cached = self.cache.get(self.cache_key)
        self.assertNotEqual(getattr(cached, "site_name", None), "Rolled back")
        self.assertEqual(SiteConfiguration.get_solo().site_name, "Committed")

"""Shared test helpers."""

from django.core.cache import cache


class CacheClearingMixin:
    """
    Clear the process-global Django cache before each test.

    IO-890: cache invalidation signals (see ``signals.invalidate_*_cache``)
    are deferred to ``transaction.on_commit``. Inside Django's ``TestCase``
    the surrounding transaction is rolled back rather than committed, so
    those callbacks never fire. Without an explicit clear, financial-sum
    and frame-budget cache entries written by one test persist into the
    next test's process and appear as stale data keyed by the previous
    test's instance IDs.

    Mix this in for any test class that exercises a code path through
    ``CacheService`` (directly or via signals firing on
    ``ClassFinancial`` / ``LocationFinancial`` / ``ProjectFinancial`` /
    ``Project`` saves).

    Usage::

        class MyTest(CacheClearingMixin, TestCase):
            def setUp(self):
                super().setUp()
                ...

    Two ordering rules apply, and both fail silently if violated:

    * List ``CacheClearingMixin`` **before** ``TestCase`` in the bases.
      Python resolves MRO left-to-right and Django's ``TestCase.setUp``
      does not chain to ``super()``, so the reverse order skips the
      mixin entirely.
    * Subclasses that override ``setUp`` **must** call
      ``super().setUp()`` for the clear to run.
    """

    def setUp(self):
        cache.clear()
        super().setUp()

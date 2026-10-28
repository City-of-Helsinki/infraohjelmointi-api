"""Shared test helpers."""

from django.core.cache import cache


class CacheClearingMixin:
    """
    Clear the process-global Django cache before each test.

    Lookup-cache invalidation (see ``signals._lookup_invalidator``) is
    deferred to ``transaction.on_commit``. Inside Django's ``TestCase`` the
    surrounding transaction is rolled back rather than committed, so those
    callbacks never fire. Without an explicit clear, lookup lists cached by
    one test persist into the next.

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

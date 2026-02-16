"""
PostgreSQL operations that use TRUNCATE ... CASCADE when flushing.

This allows test teardown to succeed when tables have foreign key
relationships (e.g. ProjectPhaseDetail -> ProjectPhase) without
requiring a specific truncation order.
"""
from django.db.backends.postgresql import operations as pg_operations


class DatabaseOperations(pg_operations.DatabaseOperations):
    def sql_flush(self, style, tables, *, reset_sequences=False, allow_cascade=False):
        # Always use CASCADE so that TransactionTestCase teardown can truncate
        # tables in any order when FKs exist (e.g. projectphasedetail -> projectphase).
        return super().sql_flush(
            style, tables, reset_sequences=reset_sequences, allow_cascade=True
        )

"""
PostgreSQL backend that uses custom operations (TRUNCATE CASCADE on flush).
"""
from django.db.backends.postgresql.base import (
    DatabaseWrapper as BaseDatabaseWrapper,
)

from .operations import DatabaseOperations


class DatabaseWrapper(BaseDatabaseWrapper):
    """PostgreSQL wrapper that uses DatabaseOperations with flush CASCADE."""
    ops_class = DatabaseOperations

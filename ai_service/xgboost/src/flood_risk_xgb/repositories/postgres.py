"""Future PostgreSQL repository boundary.

The backend team owns the final SQLAlchemy models and table names. This module deliberately
contains no hard-coded ORM model imports yet. Implement the repository protocols after the team
resolves the decisions documented in docs/DB_INTEGRATION_NOTES.md.
"""

from __future__ import annotations


class PostgresRepositoryNotConfigured(RuntimeError):
    pass


def build_postgres_repositories(database_url: str):
    raise PostgresRepositoryNotConfigured(
        "PostgreSQL repositories are intentionally not wired yet. "
        "Confirm table names, status mappings, nullable unknown fields, and model-version fields "
        "with the backend owner before implementing this adapter."
    )

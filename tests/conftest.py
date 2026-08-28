"""Test configuration — ensures proper isolation and environment."""

import os

# Force testing environment before any app imports
os.environ["ENVIRONMENT"] = "testing"

# Use SQLite for tests unless PostgreSQL is explicitly available
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///./panagah_test.db"
elif os.environ["DATABASE_URL"].startswith("postgresql"):
    # Check if psycopg2 is available; if not, fall back to SQLite
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        os.environ["DATABASE_URL"] = "sqlite:///./panagah_test.db"

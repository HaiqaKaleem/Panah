"""Test configuration — ensures proper isolation and environment."""

import os

# Force testing environment before any app imports
os.environ["ENVIRONMENT"] = "testing"

# Always use SQLite for tests — fast, no server needed, deterministic
# Tests don't need PostgreSQL; the integration is tested via the Docker job.
os.environ["DATABASE_URL"] = "sqlite:///./panagah_test.db"

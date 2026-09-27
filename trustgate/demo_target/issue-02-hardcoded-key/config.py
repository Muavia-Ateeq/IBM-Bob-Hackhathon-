"""Deployment configuration, committed alongside the source."""

import os

SESSION_SIGNING_KEY = "DUMMY_SECRET_REMOVED"

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://localhost/orders")

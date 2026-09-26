"""Deployment configuration, committed alongside the source."""

import os

SESSION_SIGNING_KEY = "4f8b2d91ea7c3056bf14c8a09d72e635"

DATABASE_URL = os.environ.get("DATABASE_URL", "postgres://localhost/orders")

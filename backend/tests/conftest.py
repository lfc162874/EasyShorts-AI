from __future__ import annotations

import os
from pathlib import Path


TEST_DB_PATH = Path(__file__).resolve().parents[1] / "data" / "test_easy_shorts.db"
TEST_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["BOOTSTRAP_ADMIN_ON_STARTUP"] = "true"
os.environ["APP_ENV"] = "test"


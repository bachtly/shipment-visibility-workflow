"""
Shared pytest fixtures.

DBOS workflows require a live Postgres instance.
Set DBOS_SYSTEM_DATABASE_URL / DATABASE_URL to a test DB before running.
In CI the docker-compose postgres service is used (see ci.yml).
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Ensure env vars have defaults for local runs without .env
os.environ.setdefault("DBOS_SYSTEM_DATABASE_URL", "postgresql://shipvis:shipvis@localhost:5433/shipvis")
os.environ.setdefault("DATABASE_URL", "postgresql://shipvis:shipvis@localhost:5433/shipvis")


@pytest.fixture(scope="session")
def client():
    from app.main import app
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def db_session():
    from app.db import get_engine
    with Session(get_engine()) as s:
        yield s

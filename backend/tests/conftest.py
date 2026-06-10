"""Shared pytest fixtures.

Tests run against a real ephemeral mongod (MongoDB 8 must be installed and on
PATH). A single mongod is started per test session on a free port with a
throwaway data dir; each test gets a freshly-named database for isolation.
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
import time
import uuid

import pymongo
import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from app.core.config import settings
from app.core.db import DOCUMENT_MODELS


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def mongo_uri():
    """Start an ephemeral mongod for the test session; yield its URI."""
    mongod = shutil.which("mongod")
    if mongod is None:
        pytest.skip("mongod not found on PATH; install MongoDB to run DB tests")

    port = _free_port()
    dbpath = tempfile.mkdtemp(prefix="aurora_test_mongo_")
    proc = subprocess.Popen(
        [
            mongod,
            "--dbpath", dbpath,
            "--port", str(port),
            "--bind_ip", "127.0.0.1",
            "--quiet",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    uri = f"mongodb://127.0.0.1:{port}"
    # Wait until mongod accepts connections.
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            c = pymongo.MongoClient(uri, serverSelectionTimeoutMS=300)
            c.admin.command("ping")
            c.close()
            break
        except Exception:
            if proc.poll() is not None:
                raise RuntimeError("mongod exited during startup")
            time.sleep(0.2)
    else:
        proc.terminate()
        raise RuntimeError("mongod did not become ready in time")

    yield uri

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    shutil.rmtree(dbpath, ignore_errors=True)


@pytest_asyncio.fixture
async def db(mongo_uri):
    """Initialize Beanie against a fresh database for this test."""
    db_name = f"aurora_test_{uuid.uuid4().hex[:8]}"
    client = AsyncMongoClient(mongo_uri)
    await init_beanie(database=client[db_name], document_models=DOCUMENT_MODELS)
    yield client
    await client.drop_database(db_name)
    await client.close()


@pytest_asyncio.fixture
async def client(mongo_uri, monkeypatch):
    """ASGI test client wired to a fresh database via the real init_db path."""
    db_name = f"aurora_test_{uuid.uuid4().hex[:8]}"
    monkeypatch.setattr(settings, "mongodb_uri", mongo_uri)
    monkeypatch.setattr(settings, "mongodb_db", db_name)

    from app.main import create_app

    app = create_app()
    async with LifespanManager(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    cleanup = AsyncMongoClient(mongo_uri)
    await cleanup.drop_database(db_name)
    await cleanup.close()

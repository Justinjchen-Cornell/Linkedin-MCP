import os
import tempfile

os.environ["LINKEDIN_WORKBENCH_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_db():
    from app import models  # noqa: F401
    from app.db import engine, init_db
    from sqlmodel import SQLModel

    SQLModel.metadata.drop_all(engine)
    init_db()
    yield

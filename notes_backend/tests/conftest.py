import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from src.api.main import app
from src.api.storage.notes_store import NotesStore


@pytest.fixture()
def client(monkeypatch, tmp_path: Path) -> TestClient:
    """
    Creates a TestClient with an isolated NotesStore that writes to a tmp JSON file.

    The notes router uses a module-level `store` singleton. For test isolation, we
    monkeypatch that singleton to point to a per-test temp file.
    """
    store_path = tmp_path / "notes.json"
    store_path.write_text(json.dumps({"notes": []}), encoding="utf-8")

    # Import inside fixture so monkeypatch always applies for each test.
    from src.api.routers import notes as notes_router

    test_store = NotesStore(file_path=str(store_path))
    monkeypatch.setattr(notes_router, "store", test_store, raising=True)

    return TestClient(app)

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

import pytest
from starlette.testclient import TestClient


def _assert_note_shape(note: Dict[str, Any]) -> None:
    """Basic shape assertions for NoteOut."""
    assert isinstance(note["id"], str) and note["id"]
    assert isinstance(note["title"], str)
    assert isinstance(note["content"], str)
    # The API returns ISO timestamps.
    datetime.fromisoformat(note["created_at"])
    datetime.fromisoformat(note["updated_at"])


def _create_note(client: TestClient, title: str = "My title", content: str = "Body") -> Dict[str, Any]:
    res = client.post("/notes", json={"title": title, "content": content})
    assert res.status_code == 201, res.text
    note = res.json()
    _assert_note_shape(note)
    assert note["title"] == title
    assert note["content"] == content
    return note


def test_health_endpoint(client: TestClient) -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_get_notes_empty(client: TestClient) -> None:
    res = client.get("/notes")
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.parametrize(
    "payload",
    [
        {},  # missing required field
        {"title": ""},  # min_length validation (pydantic)
        {"title": "   "},  # router strips then rejects
    ],
)
def test_post_notes_validation_errors(client: TestClient, payload: Dict[str, Any]) -> None:
    res = client.post("/notes", json=payload)
    assert res.status_code == 422


def test_post_notes_success_then_get_list(client: TestClient) -> None:
    created = _create_note(client, title="Test note", content="hello")

    res = client.get("/notes")
    assert res.status_code == 200
    notes = res.json()
    assert isinstance(notes, list)
    assert len(notes) == 1
    assert notes[0]["id"] == created["id"]
    assert notes[0]["title"] == "Test note"
    assert notes[0]["content"] == "hello"


def test_get_note_by_id(client: TestClient) -> None:
    created = _create_note(client, title="One", content="C1")

    res = client.get(f"/notes/{created['id']}")
    assert res.status_code == 200
    note = res.json()
    _assert_note_shape(note)
    assert note["id"] == created["id"]
    assert note["title"] == "One"
    assert note["content"] == "C1"


def test_get_note_not_found(client: TestClient) -> None:
    res = client.get("/notes/not-a-real-id")
    assert res.status_code == 404
    assert res.json()["detail"] == "Note not found."


def test_put_note_updates(client: TestClient) -> None:
    created = _create_note(client, title="Before", content="Old")
    res = client.put(f"/notes/{created['id']}", json={"title": "After", "content": "New"})
    assert res.status_code == 200, res.text
    updated = res.json()
    _assert_note_shape(updated)

    assert updated["id"] == created["id"]
    assert updated["title"] == "After"
    assert updated["content"] == "New"
    # Ensure updated_at changes or is at least >= created timestamp
    assert datetime.fromisoformat(updated["updated_at"]) >= datetime.fromisoformat(created["updated_at"])


def test_put_note_validation_error(client: TestClient) -> None:
    created = _create_note(client, title="Before", content="Old")
    res = client.put(f"/notes/{created['id']}", json={"title": "   ", "content": "New"})
    assert res.status_code == 422


def test_put_note_not_found(client: TestClient) -> None:
    res = client.put("/notes/does-not-exist", json={"title": "X", "content": "Y"})
    assert res.status_code == 404
    assert res.json()["detail"] == "Note not found."


def test_delete_note_then_404(client: TestClient) -> None:
    created = _create_note(client, title="Delete me", content="bye")

    res = client.delete(f"/notes/{created['id']}")
    assert res.status_code == 204
    assert res.text == ""  # 204 should not return a body

    res2 = client.get(f"/notes/{created['id']}")
    assert res2.status_code == 404


def test_delete_note_not_found(client: TestClient) -> None:
    res = client.delete("/notes/does-not-exist")
    assert res.status_code == 404
    assert res.json()["detail"] == "Note not found."


def test_api_prefix_compatibility_routes(client: TestClient) -> None:
    # Ensure `/api/notes` behaves like `/notes`
    res = client.get("/api/notes")
    assert res.status_code == 200
    assert res.json() == []

    created = client.post("/api/notes", json={"title": "Via API prefix", "content": "Hello"}).json()
    assert "id" in created

    res2 = client.get("/api/notes")
    assert res2.status_code == 200
    assert len(res2.json()) == 1
    assert res2.json()[0]["title"] == "Via API prefix"


def test_cors_preflight_allows_frontend_origin(client: TestClient) -> None:
    # Typical browser preflight for JSON POST.
    res = client.options(
        "/notes",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert "POST" in (res.headers.get("access-control-allow-methods") or "")
    # Starlette echoes back requested headers when allow_headers=["*"]
    assert "content-type" in (res.headers.get("access-control-allow-headers") or "").lower()


def test_cors_preflight_rejects_disallowed_origin(client: TestClient) -> None:
    res = client.options(
        "/notes",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Starlette CORSMiddleware returns 400 for disallowed origin preflight.
    assert res.status_code == 400
    assert res.headers.get("access-control-allow-origin") is None

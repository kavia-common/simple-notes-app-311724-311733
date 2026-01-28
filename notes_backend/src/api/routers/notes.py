from __future__ import annotations

import os
from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from src.api.schemas.notes import NoteCreate, NoteOut, NoteUpdate
from src.api.storage.notes_store import NotesStore

router = APIRouter(prefix="/notes", tags=["Notes"])

_DATA_DIR = os.path.join(os.getcwd(), "data")
_STORE_PATH = os.path.join(_DATA_DIR, "notes.json")
store = NotesStore(file_path=_STORE_PATH)


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str = Field(..., description="Human-readable error message.")


def _to_note_out(raw: dict) -> NoteOut:
    # Stored timestamps are ISO strings.
    return NoteOut(
        id=raw["id"],
        title=raw["title"],
        content=raw.get("content", ""),
        created_at=datetime.fromisoformat(raw["created_at"]),
        updated_at=datetime.fromisoformat(raw["updated_at"]),
    )


@router.get(
    "",
    response_model=List[NoteOut],
    summary="List notes",
    description="Returns all notes, sorted by most recently updated.",
    operation_id="list_notes",
    responses={200: {"description": "List of notes."}},
)
# PUBLIC_INTERFACE
def list_notes():
    """List all notes.

    Returns:
        List[NoteOut]: Notes sorted by last update time (descending).
    """
    notes = store.list_notes()
    return [_to_note_out(n) for n in notes]


@router.post(
    "",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a note",
    description="Creates a new note. Title must be non-empty.",
    operation_id="create_note",
    responses={
        201: {"description": "Created note."},
        422: {"description": "Validation error."},
    },
)
# PUBLIC_INTERFACE
def create_note(payload: NoteCreate):
    """Create a note.

    Args:
        payload (NoteCreate): The note to create.

    Returns:
        NoteOut: The created note.
    """
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title must be non-empty.")

    note = store.create_note(title=title, content=payload.content)
    return _to_note_out(note)


@router.get(
    "/{note_id}",
    response_model=NoteOut,
    summary="Get a note",
    description="Fetch a single note by its ID.",
    operation_id="get_note",
    responses={
        200: {"description": "The note."},
        404: {"model": ErrorResponse, "description": "Note not found."},
    },
)
# PUBLIC_INTERFACE
def get_note(note_id: str):
    """Get a note by ID.

    Args:
        note_id (str): Note ID.

    Returns:
        NoteOut: The note.

    Raises:
        HTTPException: 404 if not found.
    """
    note = store.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return _to_note_out(note)


@router.put(
    "/{note_id}",
    response_model=NoteOut,
    summary="Update a note",
    description="Update title/content for an existing note. Title must be non-empty.",
    operation_id="update_note",
    responses={
        200: {"description": "Updated note."},
        404: {"model": ErrorResponse, "description": "Note not found."},
        422: {"description": "Validation error."},
    },
)
# PUBLIC_INTERFACE
def update_note(note_id: str, payload: NoteUpdate):
    """Update a note by ID.

    Args:
        note_id (str): Note ID.
        payload (NoteUpdate): Updated values.

    Returns:
        NoteOut: The updated note.
    """
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Title must be non-empty.")

    updated = store.update_note(note_id=note_id, title=title, content=payload.content)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return _to_note_out(updated)


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
    description="Deletes a note by ID.",
    operation_id="delete_note",
    responses={
        204: {"description": "Deleted."},
        404: {"model": ErrorResponse, "description": "Note not found."},
    },
)
# PUBLIC_INTERFACE
def delete_note(note_id: str):
    """Delete a note by ID.

    Args:
        note_id (str): Note ID.

    Returns:
        Response: 204 No Content on success.
    """
    ok = store.delete_note(note_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

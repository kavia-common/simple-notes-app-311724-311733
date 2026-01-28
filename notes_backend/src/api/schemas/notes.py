from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Payload for creating a note."""

    title: str = Field(..., description="Non-empty note title.", min_length=1, max_length=200)
    content: str = Field("", description="Note content/body.", max_length=50_000)


class NoteUpdate(BaseModel):
    """Payload for updating a note."""

    title: str = Field(..., description="Non-empty note title.", min_length=1, max_length=200)
    content: str = Field("", description="Note content/body.", max_length=50_000)


class NoteOut(BaseModel):
    """Note representation returned by the API."""

    id: str = Field(..., description="Unique note ID.")
    title: str = Field(..., description="Note title.")
    content: str = Field(..., description="Note content/body.")
    created_at: datetime = Field(..., description="When the note was created (UTC).")
    updated_at: datetime = Field(..., description="When the note was last updated (UTC).")

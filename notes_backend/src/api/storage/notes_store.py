from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotesStore:
    """A tiny JSON-file backed store for notes.

    This is designed for preview/local environments without a database.
    It uses a simple in-process lock to serialize file read/writes.
    """

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._lock = threading.Lock()

        # Ensure directory exists
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

        # Create the file if it doesn't exist
        if not os.path.exists(self._file_path):
            self._write_all({"notes": []})

    def _read_all(self) -> dict:
        with open(self._file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_all(self, data: dict) -> None:
        tmp_path = f"{self._file_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp_path, self._file_path)

    def list_notes(self) -> List[Dict]:
        with self._lock:
            data = self._read_all()
            notes = data.get("notes", [])
            # Sort by updated_at desc, then created_at desc
            def key(n: Dict) -> str:
                return n.get("updated_at") or n.get("created_at") or ""

            return sorted(notes, key=key, reverse=True)

    def get_note(self, note_id: str) -> Optional[Dict]:
        with self._lock:
            data = self._read_all()
            for n in data.get("notes", []):
                if n.get("id") == note_id:
                    return n
            return None

    def create_note(self, title: str, content: str) -> Dict:
        with self._lock:
            data = self._read_all()
            now = _utcnow()

            note = {
                "id": str(uuid.uuid4()),
                "title": title,
                "content": content,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
            data.setdefault("notes", []).append(note)
            self._write_all(data)
            return note

    def update_note(self, note_id: str, title: str, content: str) -> Optional[Dict]:
        with self._lock:
            data = self._read_all()
            notes = data.get("notes", [])
            for idx, n in enumerate(notes):
                if n.get("id") == note_id:
                    now = _utcnow()
                    updated = {
                        **n,
                        "title": title,
                        "content": content,
                        "updated_at": now.isoformat(),
                    }
                    notes[idx] = updated
                    data["notes"] = notes
                    self._write_all(data)
                    return updated
            return None

    def delete_note(self, note_id: str) -> bool:
        with self._lock:
            data = self._read_all()
            notes = data.get("notes", [])
            new_notes = [n for n in notes if n.get("id") != note_id]
            if len(new_notes) == len(notes):
                return False
            data["notes"] = new_notes
            self._write_all(data)
            return True

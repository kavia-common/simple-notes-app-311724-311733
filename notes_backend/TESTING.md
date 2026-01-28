# Backend API tests (notes_backend)

## What is covered
- `GET /health`
- Notes CRUD:
  - `GET /notes` (empty and after creation)
  - `POST /notes` (validation and success)
  - `GET /notes/{id}`
  - `PUT /notes/{id}`
  - `DELETE /notes/{id}`
- Compatibility routes under `/api/notes`
- CORS/OPTIONS preflight behavior for the frontend origin (`http://localhost:3000`)

## How tests avoid cross-test interference
The notes router uses a module-level `store` that writes to a JSON file.
Each test monkeypatches that `store` to use a per-test temporary JSON file.

## Run tests
From `simple-notes-app-311724-311733/notes_backend`:

```bash
pytest
```

If you want more output:

```bash
pytest -vv
```

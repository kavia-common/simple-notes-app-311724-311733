from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers.notes import router as notes_router

openapi_tags = [
    {"name": "Health", "description": "Service health and status endpoints."},
    {"name": "Notes", "description": "CRUD operations for notes."},
]

app = FastAPI(
    title="Simple Notes API",
    description="A simple Notes CRUD API for the preview environment. Uses a local JSON file for persistence.",
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# For preview/dev, explicitly allow the React dev server.
# If deploying elsewhere, this can be tightened further.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns a simple payload indicating the API is running.",
    operation_id="health_check",
)
# PUBLIC_INTERFACE
def health_check():
    """Health check endpoint.

    Returns:
        dict: A small payload indicating the service is healthy.
    """
    return {"status": "ok"}


app.include_router(notes_router)

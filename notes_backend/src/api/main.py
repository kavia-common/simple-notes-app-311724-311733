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
# CORS: allow the preview frontend origin (cloud) and local dev.
# In preview environments the UI is served from a kavia.ai host, so restricting
# to only http://localhost:3000 will cause browser "Failed to fetch".
app.add_middleware(
    CORSMiddleware,
    # NOTE: This app has no authentication, so we explicitly disable credentials.
    # This avoids the stricter browser CORS rules around credentialed requests
    # (and eliminates a common cause of "Failed to fetch" in preview setups).
    allow_credentials=False,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Preview environment frontend origin (note the port).
        "https://vscode-internal-19014-beta.beta01.cloud.kavia.ai:3000",
        # Also allow API/docs without specifying a port.
        "https://vscode-internal-19014-beta.beta01.cloud.kavia.ai",
    ],
    # Allow any *.cloud.kavia.ai origin, with optional port.
    allow_origin_regex=r"^https:\/\/.*\.cloud\.kavia\.ai(?::\d+)?$",
    # Be explicit about methods to satisfy strict preflight checks.
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    # Allow all headers so browser preflight does not fail if the frontend adds
    # additional headers (e.g. Authorization, X-Requested-With, etc.).
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


# Main routes
app.include_router(notes_router)

# Compatibility routes: some frontends/proxies use an `/api` prefix.
# Including the same router under `/api` prevents route-mismatch "Failed to fetch".
app.include_router(notes_router, prefix="/api")

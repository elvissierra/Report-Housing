from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
from routers import reports

# --- Application Setup ---
app = FastAPI(title="Report Auto API")

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
app.include_router(reports.router, prefix="/api")

# --- Static File Serving (The Vue App) ---

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

# Mount the static assets (JS, CSS files)
# app.mount(
#     "/assets",
#     StaticFiles(directory=os.path.join(STATIC_DIR, "assets")),
#     name="vue-assets"
# )


# --- Root Endpoint (Serves the Vue App) ---
@app.get("/")
async def serve_vue_app():
    """
    Serves the main index.html file for the Vue application.
    This is the entry point for the user interface.
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(
        {"detail": "Frontend build not found. In development, use the Vite dev server on port 5173."},
        status_code=404,
    )


# --- Optional Health Check ---
@app.get("/api/health")
def health_check():
    """A non-user-facing endpoint to confirm the API is running."""
    return {"status": "ok"}

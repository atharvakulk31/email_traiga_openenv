"""
Email Triage OpenEnv — FastAPI server entry point.

Run (development):
    uvicorn backend.main:app --reload --port 8000

Run (production / Docker):
    uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api.routes import router


# ── OpenEnv root-level path rewrite middleware ─────────────────────────────────
# The OpenEnv validator hits /reset, /step, /state directly (no /api prefix).
# This middleware rewrites those paths to /api/* before routing.
# Pure ASGI middleware — rewrites /reset /step /state /health → /api/*
# BaseHTTPMiddleware breaks POST body; raw ASGI avoids that entirely.
class OpenEnvPathRewrite:
    def __init__(self, app):
        self.app = app

    # All root-level paths that the OpenEnv validator may call without /api prefix
    _REWRITE_PATHS = {
        "/reset", "/step", "/state", "/health",
        "/tasks", "/graders", "/emails", "/schema",
        "/metadata", "/triage", "/agent",
    }

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            # Also rewrite /tasks/{id} style paths
            if path in self._REWRITE_PATHS or any(
                path.startswith(p + "/") for p in self._REWRITE_PATHS
            ):
                scope = dict(scope)
                scope["path"]     = "/api" + path
                scope["raw_path"] = ("/api" + path).encode("utf-8")
        await self.app(scope, receive, send)

app = FastAPI(
    title="Email Triage OpenEnv API",
    description=(
        "AI-powered email triage environment compliant with the OpenEnv specification. "
        "Supports agent evaluation through programmatic graders for category classification, "
        "priority detection, and reply generation tasks."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(OpenEnvPathRewrite)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Serve built React frontend in production
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    # Known API paths that should NEVER be caught by the SPA catch-all.
    # If the validator hits an endpoint we don't have, it should get a 404 (not HTML).
    _API_PREFIXES = (
        "api/", "reset", "step", "state", "health", "tasks", "schema",
        "metadata", "graders", "emails", "triage", "agent", "docs",
        "redoc", "openapi.json", "mcp",
    )

    @app.get("/", include_in_schema=False)
    async def serve_spa_root():
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str = ""):
        # Never serve HTML for API-like paths — let them 404 properly
        if full_path.lower().startswith(_API_PREFIXES):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        index = os.path.join(FRONTEND_DIST, "index.html")
        if os.path.isfile(index):
            return FileResponse(index)
        return {"message": "Frontend not built. Run: cd frontend && npm run build"}
else:
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Email Triage OpenEnv API",
            "docs": "/docs",
            "health": "/api/health",
            "version": "1.0.0",
            "frontend": "Run 'cd frontend && npm run dev' for the UI"
        }

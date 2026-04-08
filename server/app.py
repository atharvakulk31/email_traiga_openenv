# server/app.py — OpenEnv server entry point
# This file is required by openenv validate for multi-mode deployment.
# It re-exports the FastAPI app from backend.main.

from backend.main import app

__all__ = ["app"]

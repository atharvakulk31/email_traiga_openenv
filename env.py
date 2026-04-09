# env.py — Scaler meta-hackathon-v1 flat entry point.
#
# Scaler's Phase 2 validator expects a top-level `env:app` FastAPI instance
# (matching the reference sample). This file simply re-exports the backend
# app so both `uvicorn env:app` and `uvicorn backend.main:app` work.

from backend.main import app

__all__ = ["app"]

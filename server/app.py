# server/app.py — OpenEnv server entry point
# This file is required by openenv validate for multi-mode deployment.
# It re-exports the FastAPI app from backend.main.

import uvicorn
from backend.main import app

__all__ = ["app", "main"]


def main():
    """Launch the Email Triage OpenEnv server."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()

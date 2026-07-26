"""CLI entry point to run the ScriptLens structure API."""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Start the FastAPI server with uvicorn."""
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
    )


if __name__ == "__main__":
    main()

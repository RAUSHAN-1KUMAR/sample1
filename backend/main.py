"""FastAPI application entrypoint for The Pitch Visualizer backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.storyboard import router as storyboard_router

app = FastAPI(title="The Pitch Visualizer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(storyboard_router, prefix="/api")


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    """Simple health endpoint for local sanity checks."""
    return {"status": "ok"}

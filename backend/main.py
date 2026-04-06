"""FastAPI backend for prompt-to-simulation web app."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from prompt_parser import parse_prompt
from simulation_runner import run_simulation

app = FastAPI(title="Prompt Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


class GenerateRequest(BaseModel):
    prompt: str
    steps: int = 100


class RunRequest(BaseModel):
    spec: dict
    params: dict | None = None
    steps: int = 100


@app.post("/generate")
def generate(req: GenerateRequest):
    """Parse prompt → spec → run simulation → return results."""
    spec = parse_prompt(req.prompt)
    result = run_simulation(spec, steps=req.steps)
    return {"spec": spec, "result": result}


@app.post("/run")
def run(req: RunRequest):
    """Re-run simulation with modified params."""
    result = run_simulation(req.spec, params=req.params, steps=req.steps)
    return {"result": result}


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve frontend static files
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """Serve the React SPA for any non-API route."""
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")

"""FastAPI backend for prompt-to-simulation web app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

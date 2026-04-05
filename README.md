# Prompt Simulator

Describe a system. Watch it simulate. Tweak it live.

A web app that converts natural language prompts into interactive agent-based simulations using Mesa.

## Supported Simulation Types

- **Spread/Contagion** - rumors, viruses, fire spreading
- **Crowd Movement** - pedestrians, evacuation, flocking
- **Traffic Flow** - cars, lane switching, aggressive drivers
- **Market Adoption** - product adoption, consumer behavior

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## How It Works

1. Enter a natural language prompt (e.g. "simulate people spreading a rumor in a crowded space")
2. The backend parses the prompt into a structured simulation spec
3. Mesa runs the simulation for 100 steps
4. The frontend animates the results on a 2D canvas
5. Adjust parameters with sliders and re-run instantly

## Architecture

```
Prompt → Parser → Structured Spec → Simulation Runner → Frames + Metrics → Canvas Renderer
```

- **Backend**: FastAPI + Mesa (Python)
- **Frontend**: React + Vite + Canvas API
- **Pipeline**: Prompt → Spec → Simulation → Visualization (no arbitrary code generation)

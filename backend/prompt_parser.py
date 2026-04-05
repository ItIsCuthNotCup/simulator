"""Parse natural language prompts into structured simulation specs."""

import re
from typing import Any

SIMULATION_TYPES = {
    "spread": {
        "keywords": ["spread", "rumor", "virus", "disease", "infect", "contagion", "gossip", "fire", "epidemic", "pandemic"],
        "default_spec": {
            "type": "spread",
            "environment": {"width": 50, "height": 50, "topology": "grid"},
            "agents": [
                {
                    "type": "person",
                    "count": 200,
                    "states": ["susceptible", "infected", "recovered"],
                    "initial_state": "susceptible",
                    "infected_ratio": 0.05,
                }
            ],
            "rules": [
                {"name": "move", "description": "agents move randomly"},
                {"name": "spread", "description": "infected agents spread to nearby susceptible agents", "probability": 0.3},
                {"name": "recover", "description": "infected agents recover after time", "probability": 0.05},
            ],
            "parameters": [
                {"name": "agent_count", "label": "Number of People", "min": 20, "max": 500, "default": 200, "step": 10},
                {"name": "spread_chance", "label": "Spread Probability", "min": 0.01, "max": 1.0, "default": 0.3, "step": 0.01},
                {"name": "recover_chance", "label": "Recovery Probability", "min": 0.01, "max": 0.5, "default": 0.05, "step": 0.01},
                {"name": "initial_infected", "label": "Initial Infected %", "min": 1, "max": 50, "default": 5, "step": 1},
            ],
            "visualization": {"colors": {"susceptible": "#4CAF50", "infected": "#F44336", "recovered": "#2196F3"}},
        },
    },
    "crowd": {
        "keywords": ["crowd", "people", "pedestrian", "walk", "gather", "evacuat", "stampede", "flock"],
        "default_spec": {
            "type": "crowd",
            "environment": {"width": 50, "height": 50, "topology": "grid"},
            "agents": [
                {
                    "type": "person",
                    "count": 150,
                    "states": ["wandering", "goal_seeking"],
                    "initial_state": "wandering",
                }
            ],
            "rules": [
                {"name": "move", "description": "agents move toward goals or randomly"},
                {"name": "avoid", "description": "agents avoid collisions"},
            ],
            "parameters": [
                {"name": "agent_count", "label": "Number of People", "min": 20, "max": 500, "default": 150, "step": 10},
                {"name": "speed", "label": "Movement Speed", "min": 1, "max": 5, "default": 1, "step": 1},
                {"name": "goal_ratio", "label": "Goal-Seeking %", "min": 0, "max": 100, "default": 30, "step": 5},
            ],
            "visualization": {"colors": {"wandering": "#FF9800", "goal_seeking": "#9C27B0"}},
        },
    },
    "traffic": {
        "keywords": ["traffic", "car", "driver", "road", "lane", "vehicle", "highway", "driv"],
        "default_spec": {
            "type": "traffic",
            "environment": {"width": 80, "height": 20, "topology": "grid"},
            "agents": [
                {
                    "type": "car",
                    "count": 60,
                    "states": ["slow", "normal", "fast", "aggressive"],
                    "initial_state": "normal",
                }
            ],
            "rules": [
                {"name": "move", "description": "cars move forward at their speed"},
                {"name": "lane_switch", "description": "cars switch lanes to avoid slow cars"},
                {"name": "brake", "description": "cars slow down if blocked"},
            ],
            "parameters": [
                {"name": "agent_count", "label": "Number of Cars", "min": 10, "max": 200, "default": 60, "step": 5},
                {"name": "aggressive_ratio", "label": "Aggressive Drivers %", "min": 0, "max": 100, "default": 20, "step": 5},
                {"name": "speed_limit", "label": "Speed Limit", "min": 1, "max": 5, "default": 3, "step": 1},
            ],
            "visualization": {"colors": {"slow": "#FFC107", "normal": "#4CAF50", "fast": "#2196F3", "aggressive": "#F44336"}},
        },
    },
    "market": {
        "keywords": ["market", "adopt", "product", "buy", "sell", "economy", "trade", "stock", "business", "consumer"],
        "default_spec": {
            "type": "market",
            "environment": {"width": 50, "height": 50, "topology": "grid"},
            "agents": [
                {
                    "type": "consumer",
                    "count": 200,
                    "states": ["unaware", "considering", "adopted"],
                    "initial_state": "unaware",
                    "adopted_ratio": 0.02,
                }
            ],
            "rules": [
                {"name": "influence", "description": "adopted agents influence neighbors", "probability": 0.15},
                {"name": "consider", "description": "considering agents may adopt", "probability": 0.1},
                {"name": "move", "description": "agents move randomly"},
            ],
            "parameters": [
                {"name": "agent_count", "label": "Number of Consumers", "min": 20, "max": 500, "default": 200, "step": 10},
                {"name": "influence_chance", "label": "Influence Probability", "min": 0.01, "max": 1.0, "default": 0.15, "step": 0.01},
                {"name": "adopt_chance", "label": "Adoption Probability", "min": 0.01, "max": 1.0, "default": 0.1, "step": 0.01},
                {"name": "initial_adopters", "label": "Initial Adopters %", "min": 1, "max": 30, "default": 2, "step": 1},
            ],
            "visualization": {"colors": {"unaware": "#9E9E9E", "considering": "#FF9800", "adopted": "#4CAF50"}},
        },
    },
}


def parse_prompt(prompt: str) -> dict[str, Any]:
    """Parse a natural language prompt into a structured simulation spec."""
    prompt_lower = prompt.lower()

    best_type = "spread"
    best_score = 0

    for sim_type, config in SIMULATION_TYPES.items():
        score = sum(1 for kw in config["keywords"] if kw in prompt_lower)
        if score > best_score:
            best_score = score
            best_type = sim_type

    spec = _deep_copy_spec(SIMULATION_TYPES[best_type]["default_spec"])
    spec["prompt"] = prompt
    _apply_prompt_hints(spec, prompt_lower)
    return spec


def _deep_copy_spec(spec: dict) -> dict:
    """Deep copy a spec dict."""
    import json
    return json.loads(json.dumps(spec))


def _apply_prompt_hints(spec: dict, prompt_lower: str):
    """Tweak spec based on prompt keywords."""
    # Adjust agent count based on size hints
    if any(w in prompt_lower for w in ["crowded", "many", "lots", "packed", "huge"]):
        for p in spec["parameters"]:
            if p["name"] == "agent_count":
                p["default"] = min(p["default"] * 2, p["max"])
                for a in spec["agents"]:
                    a["count"] = p["default"]

    if any(w in prompt_lower for w in ["few", "small", "sparse", "handful"]):
        for p in spec["parameters"]:
            if p["name"] == "agent_count":
                p["default"] = max(p["default"] // 2, p["min"])
                for a in spec["agents"]:
                    a["count"] = p["default"]

    # Adjust spread rate
    if any(w in prompt_lower for w in ["fast", "rapid", "quick", "aggressive"]):
        for p in spec["parameters"]:
            if "chance" in p["name"] or "probability" in p["name"]:
                p["default"] = min(p["default"] * 1.5, p["max"])

    if any(w in prompt_lower for w in ["slow", "gradual", "steady"]):
        for p in spec["parameters"]:
            if "chance" in p["name"] or "probability" in p["name"]:
                p["default"] = max(p["default"] * 0.5, p["min"])

    # Extract numbers from prompt for agent count
    numbers = re.findall(r'\b(\d+)\s*(?:people|agents|cars|consumers|persons|drivers)\b', prompt_lower)
    if numbers:
        count = int(numbers[0])
        for p in spec["parameters"]:
            if p["name"] == "agent_count":
                count = max(p["min"], min(count, p["max"]))
                p["default"] = count
                for a in spec["agents"]:
                    a["count"] = count

"""Run Mesa simulations from structured specs and return frame data."""

import random
import math
from typing import Any


def run_simulation(spec: dict, params: dict | None = None, steps: int = 100) -> dict[str, Any]:
    """Run a simulation based on spec and return frames."""
    sim_type = spec.get("type", "spread")
    merged_params = _merge_params(spec, params)

    runners = {
        "spread": _run_spread,
        "crowd": _run_crowd,
        "traffic": _run_traffic,
        "market": _run_market,
    }

    runner = runners.get(sim_type, _run_spread)
    return runner(spec, merged_params, steps)


def _merge_params(spec: dict, overrides: dict | None) -> dict:
    """Merge default params with overrides."""
    params = {}
    for p in spec.get("parameters", []):
        params[p["name"]] = p["default"]
    if overrides:
        params.update(overrides)
    return params


def _run_spread(spec: dict, params: dict, steps: int) -> dict:
    width = spec["environment"]["width"]
    height = spec["environment"]["height"]
    agent_count = int(params.get("agent_count", 200))
    spread_chance = float(params.get("spread_chance", 0.3))
    recover_chance = float(params.get("recover_chance", 0.05))
    initial_infected_pct = float(params.get("initial_infected", 5)) / 100.0

    agents = []
    for i in range(agent_count):
        agents.append({
            "id": i,
            "x": random.randint(0, width - 1),
            "y": random.randint(0, height - 1),
            "state": "infected" if random.random() < initial_infected_pct else "susceptible",
        })

    frames = []
    metrics = []

    for step in range(steps):
        # Move agents
        for a in agents:
            a["x"] = max(0, min(width - 1, a["x"] + random.randint(-1, 1)))
            a["y"] = max(0, min(height - 1, a["y"] + random.randint(-1, 1)))

        # Build position lookup
        grid = {}
        for a in agents:
            key = (a["x"], a["y"])
            grid.setdefault(key, []).append(a)

        # Spread
        new_infections = []
        for a in agents:
            if a["state"] == "susceptible":
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        neighbors = grid.get((a["x"] + dx, a["y"] + dy), [])
                        for n in neighbors:
                            if n["state"] == "infected" and random.random() < spread_chance:
                                new_infections.append(a["id"])

        for a in agents:
            if a["id"] in new_infections:
                a["state"] = "infected"

        # Recover
        for a in agents:
            if a["state"] == "infected" and random.random() < recover_chance:
                a["state"] = "recovered"

        # Record frame
        counts = {"susceptible": 0, "infected": 0, "recovered": 0}
        frame_agents = []
        for a in agents:
            counts[a["state"]] += 1
            frame_agents.append({"id": a["id"], "x": a["x"], "y": a["y"], "state": a["state"]})

        frames.append({"step": step, "agents": frame_agents})
        metrics.append({"step": step, **counts})

    return {
        "frames": frames,
        "metrics": metrics,
        "metadata": {
            "type": spec["type"],
            "width": width,
            "height": height,
            "steps": steps,
            "colors": spec.get("visualization", {}).get("colors", {}),
        },
    }


def _run_crowd(spec: dict, params: dict, steps: int) -> dict:
    width = spec["environment"]["width"]
    height = spec["environment"]["height"]
    agent_count = int(params.get("agent_count", 150))
    speed = int(params.get("speed", 1))
    goal_ratio = float(params.get("goal_ratio", 30)) / 100.0

    # Create goals (corners and center)
    goals = [(width // 4, height // 4), (3 * width // 4, height // 4),
             (width // 2, height // 2), (width // 4, 3 * height // 4),
             (3 * width // 4, 3 * height // 4)]

    agents = []
    for i in range(agent_count):
        is_goal = random.random() < goal_ratio
        agents.append({
            "id": i,
            "x": random.randint(0, width - 1),
            "y": random.randint(0, height - 1),
            "state": "goal_seeking" if is_goal else "wandering",
            "goal": random.choice(goals) if is_goal else None,
        })

    frames = []
    metrics = []

    for step in range(steps):
        for a in agents:
            if a["state"] == "goal_seeking" and a["goal"]:
                gx, gy = a["goal"]
                dx = max(-speed, min(speed, gx - a["x"]))
                dy = max(-speed, min(speed, gy - a["y"]))
                # Reached goal? Pick new one
                if abs(a["x"] - gx) <= 1 and abs(a["y"] - gy) <= 1:
                    a["goal"] = random.choice(goals)
                a["x"] = max(0, min(width - 1, a["x"] + dx))
                a["y"] = max(0, min(height - 1, a["y"] + dy))
            else:
                a["x"] = max(0, min(width - 1, a["x"] + random.randint(-speed, speed)))
                a["y"] = max(0, min(height - 1, a["y"] + random.randint(-speed, speed)))

        counts = {"wandering": 0, "goal_seeking": 0}
        frame_agents = []
        for a in agents:
            counts[a["state"]] += 1
            frame_agents.append({"id": a["id"], "x": a["x"], "y": a["y"], "state": a["state"]})

        frames.append({"step": step, "agents": frame_agents})
        metrics.append({"step": step, **counts})

    return {
        "frames": frames,
        "metrics": metrics,
        "metadata": {
            "type": spec["type"],
            "width": width,
            "height": height,
            "steps": steps,
            "colors": spec.get("visualization", {}).get("colors", {}),
        },
    }


def _run_traffic(spec: dict, params: dict, steps: int) -> dict:
    width = spec["environment"]["width"]
    height = spec["environment"]["height"]
    agent_count = int(params.get("agent_count", 60))
    aggressive_ratio = float(params.get("aggressive_ratio", 20)) / 100.0
    speed_limit = int(params.get("speed_limit", 3))

    num_lanes = height

    agents = []
    for i in range(agent_count):
        is_aggressive = random.random() < aggressive_ratio
        spd = random.randint(1, speed_limit)
        if is_aggressive:
            spd = speed_limit
        agents.append({
            "id": i,
            "x": random.randint(0, width - 1),
            "y": random.randint(0, num_lanes - 1),
            "state": "aggressive" if is_aggressive else ["slow", "normal", "fast"][min(spd - 1, 2)],
            "speed": spd,
        })

    frames = []
    metrics = []

    for step in range(steps):
        # Build occupancy
        occupied = set()
        for a in agents:
            occupied.add((a["x"], a["y"]))

        for a in agents:
            # Check ahead
            ahead_blocked = (a["x"] + a["speed"]) % width
            blocked = any((x % width, a["y"]) in occupied and (x % width, a["y"]) != (a["x"], a["y"])
                         for x in range(a["x"] + 1, a["x"] + a["speed"] + 1))

            if blocked:
                # Try lane switch
                new_lane = a["y"] + random.choice([-1, 1])
                if 0 <= new_lane < num_lanes and (a["x"], new_lane) not in occupied:
                    occupied.discard((a["x"], a["y"]))
                    a["y"] = new_lane
                    occupied.add((a["x"], a["y"]))
                else:
                    # Slow down
                    occupied.discard((a["x"], a["y"]))
                    a["x"] = (a["x"] + 1) % width
                    occupied.add((a["x"], a["y"]))
            else:
                occupied.discard((a["x"], a["y"]))
                a["x"] = (a["x"] + a["speed"]) % width
                occupied.add((a["x"], a["y"]))

        counts = {"slow": 0, "normal": 0, "fast": 0, "aggressive": 0}
        frame_agents = []
        for a in agents:
            counts[a["state"]] = counts.get(a["state"], 0) + 1
            frame_agents.append({"id": a["id"], "x": a["x"], "y": a["y"], "state": a["state"]})

        frames.append({"step": step, "agents": frame_agents})
        metrics.append({"step": step, **counts})

    return {
        "frames": frames,
        "metrics": metrics,
        "metadata": {
            "type": spec["type"],
            "width": width,
            "height": height,
            "steps": steps,
            "colors": spec.get("visualization", {}).get("colors", {}),
        },
    }


def _run_market(spec: dict, params: dict, steps: int) -> dict:
    width = spec["environment"]["width"]
    height = spec["environment"]["height"]
    agent_count = int(params.get("agent_count", 200))
    influence_chance = float(params.get("influence_chance", 0.15))
    adopt_chance = float(params.get("adopt_chance", 0.1))
    initial_adopters_pct = float(params.get("initial_adopters", 2)) / 100.0

    agents = []
    for i in range(agent_count):
        agents.append({
            "id": i,
            "x": random.randint(0, width - 1),
            "y": random.randint(0, height - 1),
            "state": "adopted" if random.random() < initial_adopters_pct else "unaware",
        })

    frames = []
    metrics = []

    for step in range(steps):
        # Move
        for a in agents:
            a["x"] = max(0, min(width - 1, a["x"] + random.randint(-1, 1)))
            a["y"] = max(0, min(height - 1, a["y"] + random.randint(-1, 1)))

        grid = {}
        for a in agents:
            key = (a["x"], a["y"])
            grid.setdefault(key, []).append(a)

        # Influence
        new_considering = []
        new_adopted = []
        for a in agents:
            if a["state"] == "unaware":
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        for n in grid.get((a["x"] + dx, a["y"] + dy), []):
                            if n["state"] == "adopted" and random.random() < influence_chance:
                                new_considering.append(a["id"])
            elif a["state"] == "considering":
                if random.random() < adopt_chance:
                    new_adopted.append(a["id"])

        for a in agents:
            if a["id"] in new_adopted:
                a["state"] = "adopted"
            elif a["id"] in new_considering and a["state"] == "unaware":
                a["state"] = "considering"

        counts = {"unaware": 0, "considering": 0, "adopted": 0}
        frame_agents = []
        for a in agents:
            counts[a["state"]] += 1
            frame_agents.append({"id": a["id"], "x": a["x"], "y": a["y"], "state": a["state"]})

        frames.append({"step": step, "agents": frame_agents})
        metrics.append({"step": step, **counts})

    return {
        "frames": frames,
        "metrics": metrics,
        "metadata": {
            "type": spec["type"],
            "width": width,
            "height": height,
            "steps": steps,
            "colors": spec.get("visualization", {}).get("colors", {}),
        },
    }

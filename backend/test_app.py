"""End-to-end tests for the simulation app."""

import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    print("PASS: health endpoint")


def test_frontend_served():
    r = client.get("/")
    assert r.status_code == 200
    assert "<!doctype html>" in r.text.lower() or "<!DOCTYPE html>" in r.text
    assert "index-" in r.text  # JS bundle reference
    print("PASS: frontend HTML served at /")


def test_static_assets():
    # Get the JS filename from the HTML
    r = client.get("/")
    import re
    js_match = re.search(r'/assets/(index-[^"]+\.js)', r.text)
    css_match = re.search(r'/assets/(index-[^"]+\.css)', r.text)

    assert js_match, "JS bundle not found in HTML"
    js_file = js_match.group(1)
    r2 = client.get(f"/assets/{js_file}")
    assert r2.status_code == 200
    assert len(r2.content) > 1000  # JS bundle should be substantial
    print(f"PASS: JS asset served ({len(r2.content)} bytes)")

    assert css_match, "CSS bundle not found in HTML"
    css_file = css_match.group(1)
    r3 = client.get(f"/assets/{css_file}")
    assert r3.status_code == 200
    assert len(r3.content) > 100
    print(f"PASS: CSS asset served ({len(r3.content)} bytes)")


def test_generate_spread():
    r = client.post("/generate", json={
        "prompt": "simulate people spreading a rumor in a crowded space",
        "steps": 10
    })
    assert r.status_code == 200
    data = r.json()

    # Check spec
    spec = data["spec"]
    assert spec["type"] == "spread", f"Expected spread, got {spec['type']}"
    assert len(spec["parameters"]) > 0
    assert spec["agents"][0]["count"] == 400  # "crowded" doubles from 200
    print(f"PASS: prompt parsed as '{spec['type']}' with {spec['agents'][0]['count']} agents")

    # Check result
    result = data["result"]
    assert len(result["frames"]) == 10
    assert len(result["metrics"]) == 10
    assert result["metadata"]["type"] == "spread"
    assert "colors" in result["metadata"]

    # Check frame structure
    frame = result["frames"][0]
    assert "agents" in frame
    assert len(frame["agents"]) == 400
    agent = frame["agents"][0]
    assert "x" in agent and "y" in agent and "state" in agent
    assert agent["state"] in ("susceptible", "infected", "recovered")
    print(f"PASS: simulation returned {len(result['frames'])} frames with {len(frame['agents'])} agents each")

    # Check metrics
    m = result["metrics"][0]
    assert "susceptible" in m and "infected" in m and "recovered" in m
    total = m["susceptible"] + m["infected"] + m["recovered"]
    assert total == 400, f"Metrics don't sum to agent count: {total}"
    print(f"PASS: metrics correct (S={m['susceptible']} I={m['infected']} R={m['recovered']})")


def test_generate_traffic():
    r = client.post("/generate", json={
        "prompt": "simulate aggressive drivers on a highway",
        "steps": 5
    })
    assert r.status_code == 200
    data = r.json()
    assert data["spec"]["type"] == "traffic"
    assert len(data["result"]["frames"]) == 5
    print(f"PASS: traffic simulation works")


def test_generate_crowd():
    r = client.post("/generate", json={
        "prompt": "simulate a crowd evacuating a building",
        "steps": 5
    })
    assert r.status_code == 200
    data = r.json()
    assert data["spec"]["type"] == "crowd"
    print(f"PASS: crowd simulation works")


def test_generate_market():
    r = client.post("/generate", json={
        "prompt": "simulate product adoption in a consumer market",
        "steps": 5
    })
    assert r.status_code == 200
    data = r.json()
    assert data["spec"]["type"] == "market"
    print(f"PASS: market simulation works")


def test_rerun_with_params():
    # First generate
    r1 = client.post("/generate", json={"prompt": "rumor spread", "steps": 5})
    spec = r1.json()["spec"]

    # Rerun with modified params
    r2 = client.post("/run", json={
        "spec": spec,
        "params": {"agent_count": 50, "spread_chance": 0.5},
        "steps": 5
    })
    assert r2.status_code == 200
    result = r2.json()["result"]
    assert len(result["frames"]) == 5
    assert len(result["frames"][0]["agents"]) == 50
    print(f"PASS: rerun with custom params (50 agents, 0.5 spread)")


def test_spread_dynamics():
    """Verify infection actually spreads over time."""
    r = client.post("/generate", json={
        "prompt": "fast rumor spread",
        "steps": 50
    })
    data = r.json()
    metrics = data["result"]["metrics"]

    initial_infected = metrics[0]["infected"]
    final_infected = metrics[-1]["infected"]
    final_recovered = metrics[-1]["recovered"]

    # With fast spread, we should see more infected+recovered at end than start
    assert (final_infected + final_recovered) > initial_infected, \
        f"Spread didn't happen: start={initial_infected}, end_I={final_infected}, end_R={final_recovered}"
    print(f"PASS: infection spread from {initial_infected} to {final_infected}+{final_recovered} recovered over 50 steps")


if __name__ == "__main__":
    tests = [
        test_health,
        test_frontend_served,
        test_static_assets,
        test_generate_spread,
        test_generate_traffic,
        test_generate_crowd,
        test_generate_market,
        test_rerun_with_params,
        test_spread_dynamics,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed:
        exit(1)
    else:
        print("ALL TESTS PASSED")

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_algorithm_registry_and_execution_endpoint():
    algorithms = client.get("/api/v1/algorithms")
    assert algorithms.status_code == 200
    assert algorithms.json()[0]["id"] == "astar-grid"

    response = client.post(
        "/api/v1/executions",
        json={"algorithm_id": "astar-grid", "config": {"rows": 5, "cols": 5, "start": "0,0", "goal": "4,4", "obstacle_density": 0, "seed": 7}},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["events"]
    assert client.get(f"/api/v1/executions/{payload['execution_id']}").status_code == 200


def test_unknown_algorithm_returns_not_found():
    response = client.post("/api/v1/executions", json={"algorithm_id": "unknown", "config": {}})
    assert response.status_code == 404


def test_heuristic_comparison_execution_exposes_shared_problem_and_real_runs():
    response = client.post(
        "/api/v1/executions",
        json={
            "algorithm_id": "astar-heuristic-comparison",
            "config": {
                "grid": {"rows": 5, "cols": 5, "start": "0,0", "goal": "4,4", "obstacle_density": 0, "seed": 9},
                "heuristics": ["manhattan", "euclidean", "chebyshev", "zero"],
            },
        },
    )

    assert response.status_code == 200
    runs = response.json()["final_state"]["metadata"]["runs"]
    assert len(runs) == 4
    assert len({run["problem"]["signature"] for run in runs}) == 1
    assert all(run["problem"]["cost_model"] == "unit cost for each orthogonal move" for run in runs)
    assert all(run["event_count"] == len(run["events"]) for run in runs)


def test_invalid_execution_configuration_returns_unprocessable_entity():
    response = client.post(
        "/api/v1/executions",
        json={
            "algorithm_id": "astar-heuristic-comparison",
            "config": {"heuristics": ["manhattan", "manhattan"]},
        },
    )
    assert response.status_code == 422

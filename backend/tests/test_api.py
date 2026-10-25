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

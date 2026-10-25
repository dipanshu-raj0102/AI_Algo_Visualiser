# AI Algorithm Visualizer

AI Algorithm Visualizer is a production-minded foundation for learning AI algorithms by watching their real execution state change over time.

## Current slice

The first vertical slice includes:

- A FastAPI backend with a registry-driven, event-based algorithm engine.
- A real A* grid pathfinding implementation with Manhattan and Euclidean heuristics.
- Reproducible seeded grid generation and validated execution requests.
- A React + TypeScript + Vite frontend with responsive app shell, algorithm catalog, learning pages, and an interactive A* workspace.
- Playback controls for play, pause, reset, step forward, speed selection, event timeline, frontier/closed-set inspection, and metrics.
- Backend correctness tests for optimality, obstacles, and invalid configuration.

The current backend registry now includes grid search, terrain search, heuristic analysis, weighted city routing, 15-puzzle, web-crawler and landmark best-first simulations, local-search landscapes/N-Queens/TSP, generic minimax/alpha-beta, Tic-Tac-Toe, Connect-4, move-ordering analysis, and simulated-annealing scheduling. Persistence/authentication and long-lived streaming remain deliberately separate deployment phases.

## Repository layout

```text
frontend/  React + TypeScript + Vite client
backend/   FastAPI API and domain algorithm engine
docs/      Architecture and development notes
```

## Development setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`, with OpenAPI documentation at `/api/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL` when the backend is not running on `http://localhost:8000`.

### Checks

```bash
cd backend && pytest
cd frontend && npm run build
```

See [docs/architecture/overview.md](docs/architecture/overview.md), [docs/api/endpoints.md](docs/api/endpoints.md), and [docs/development/adding-algorithms.md](docs/development/adding-algorithms.md) for the extension model and API.

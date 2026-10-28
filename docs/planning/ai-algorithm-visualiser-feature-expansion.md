# AI Algorithm Visualiser — Feature Expansion, Animation System & Frontend Design Upgrade

**Planning status:** Draft overview document  
**Source:** User-supplied epic requirements  
**Jira epic:** Not provided; Jira retrieval skipped at the user's direction  
**Confluence publication:** Not performed  
**Repository:** `AI_Algo_Visualiser`

## 1. Epic Overview

### Purpose

Extend the existing AI Algorithm Visualiser into a coherent, interactive algorithm laboratory. The flagship experience is an A* Heuristic Impact Analysis that runs Manhattan, Euclidean, Chebyshev, and zero heuristics against one identical seeded grid and lets a learner inspect their different search behavior through synchronized replay, metrics, analytics, and explanation.

The epic also hardens the animation architecture and applies the existing visual language consistently across algorithm discovery, detail pages, visualizers, comparison views, responsive layouts, and accessibility behavior.

### User value

Users can move from learning an algorithm's concept to configuring a real problem, observing replayable search events, controlling playback, comparing alternatives, and understanding the measured trade-offs. The comparison makes heuristic quality concrete: path quality, search effort, frontier behavior, and completion status are visible together.

### Scope

**In scope**

- A registry-driven A* heuristic comparison using the existing A* engine.
- Exact shared-problem guarantees for grid, endpoints, obstacles, movement model, costs, and seed.
- Replayable backend events and a synchronized four-panel frontend.
- A reusable animation controller for comparison and ordinary visualizers.
- Play, pause, resume, restart, step, backward step where supported, speed, fast-forward, finish, and progress semantics.
- Real comparison metrics, deterministic educational explanation, summary table, and visual analytics.
- Consistent design tokens, grid-state semantics, responsive behavior, keyboard accessibility, focus states, and reduced-motion handling.
- Backend, frontend build/type, and Playwright verification.

**Out of scope**

- Replacing the existing algorithm registry or event architecture.
- Persistent execution storage, authentication, WebSockets, Redis, Kafka, or microservices.
- A Canvas rewrite without profiling evidence.
- Terrain-weighted heuristic comparison until the movement and cost model is explicitly extended.
- Fabricated metrics, prerecorded traces, or controls without behavior.

### Current repository baseline

The repository already implements much of the requested flagship flow:

- `backend/app/algorithms/astar_grid.py` supports the four stable heuristic identifiers and emits replayable snapshots.
- `backend/app/algorithms/heuristic_comparison.py` reuses `AStarGridEngine`, materializes one shared grid, and stores each run's trace and summary under comparison metadata.
- `backend/app/algorithms/registry.py` registers `astar-heuristic-comparison` as a `comparison-grid` feature.
- `frontend/src/features/heuristic-comparison/HeuristicComparisonPage.tsx` renders four panels, shared-problem metadata, controls, metrics, insight text, and a final table.
- `frontend/src/hooks/useAnimationController.ts` provides a generation-guarded single-timer replay controller.
- `frontend/e2e/platform.spec.ts` covers the flagship route and core playback actions.

The implementation plan therefore focuses on completing the broader epic, standardizing ordinary visualizer playback, adding analytics and deeper tests, and resolving the remaining consistency and accessibility gaps.

## 2. Epic Goals & Success Metrics

### Primary goal

Deliver a trustworthy and polished comparison laboratory in which all visible conclusions are derived from the same real execution inputs and replay events.

### Success metrics

| Measure | Target | Evidence |
|---|---:|---|
| Heuristic variants available | 4 | Registry, config validation, API, and UI |
| Shared-problem identity | 100% | One problem signature across all runs and E2E assertion |
| Comparison replay synchronization | 100% | One global cursor; completed traces remain pinned |
| Backend regression suite | 100% pass | `cd backend && pytest -q` |
| Frontend type/build check | Pass | `cd frontend && npm run build` |
| Existing and new E2E flows | 100% pass | `cd frontend && npm run e2e` |
| New controller/comparison branch coverage | Target ≥90% | Add focused test coverage or documented equivalent |
| Unhandled playback timers after restart/unmount | 0 | Controller tests and browser behavior |
| New controls with no behavioral effect | 0 | E2E state/progress assertions |
| Responsive layout regressions | 0 critical | Desktop, tablet, and mobile Playwright viewports |

### KPIs

- Median comparison load and first-render time remain within the current synchronous API's practical limits for the supported grid bounds.
- All four completed paths agree on optimal path cost for the unit-cost four-way model whenever a route exists.
- The UI reports measured expanded, discovered, frontier, explored, path, runtime, and reachability metrics without hard-coded values.
- Learners can pause, inspect, advance one event, resume, fast-forward, and restart without a page reload.

## 3. Requirements Summary

### Functional requirements

#### Comparison engine

1. Support `manhattan`, `euclidean`, `chebyshev`, and `zero` through one configurable A* implementation.
2. Materialize the grid once before variant execution. Every run receives the same rows, columns, start, goal, obstacle set, movement model, unit-cost model, and seed metadata.
3. Expose stable heuristic formulas and descriptions through backend metadata.
4. Emit sufficient replay events for a client to reconstruct frontier, explored cells, current node, path, metrics, and completion state without reimplementing search logic.
5. Produce real summaries for expanded nodes, discovered nodes, maximum frontier, search steps, execution time, path length, path cost, explored cells, reachability, and event count.
6. Preserve valid no-path and start-equals-goal behavior for every selected heuristic.
7. Keep zero heuristic explicitly documented as Dijkstra/uniform-cost search for the current four-way unit-cost model.

#### Comparison experience

1. Provide `/compare/astar-heuristics` through the existing router and algorithm discovery surfaces.
2. Render four readable panels responsively: two columns on desktop/tablet when usable, one column on narrow mobile screens.
3. Use one comparison timeline and one controller for all panels. A shorter trace stays on its terminal frame while longer traces continue.
4. Show live completion state per panel and a final comparison table based on backend metrics.
5. Add measured visual analytics: at minimum expanded-node comparison and a search-progress/frontier view. Prefer existing primitives or lightweight CSS/SVG over a new chart package.
6. Generate deterministic educational text from actual results. Claims must account for the configured movement and cost model and must not assert universal heuristic admissibility.

#### Animation system

1. Centralize playback behavior in a reusable controller or shared hook.
2. Guarantee one active timer/loop per execution and invalidate old callbacks on pause, restart, speed changes, unmount, and replacement execution.
3. Implement Play/resume, Pause, Restart, Step Forward, Step Backward where event history permits, bounded speed selection, Fast Forward, Finish, and progress.
4. Apply the same semantics to the ordinary visualizer wherever its event model supports replay.
5. Ensure speed changes affect actual delay, Fast Forward accelerates without skipping directly to completion, and Finish is the explicit terminal action.
6. Support reduced motion without losing state transitions or controls.

#### Design, responsive behavior, and accessibility

1. Reuse the established global tokens in `frontend/src/index.css` for background, surfaces, borders, text, semantic status, and visualizer states.
2. Use consistent state meanings for start, goal, obstacle, unvisited, frontier, explored, current, and final path.
3. Keep formulas, algorithm names, metrics, and technical metadata in the existing mono treatment.
4. Ensure controls are semantic buttons/selects with accessible names, visible focus, status/live announcements where useful, and no shortcut interception inside text fields.
5. Verify dark mode and responsive layouts for the flagship page and shared visualizer primitives.

### Non-functional requirements

- Preserve current React 18, FastAPI, Pydantic, Vite, and Playwright architecture.
- Maintain strict TypeScript compilation and typed Python interfaces.
- Keep event payloads bounded to the current supported grid sizes; avoid redundant payload expansion.
- Preserve deterministic structural traces while treating wall-clock runtime as inherently variable.
- Avoid new infrastructure or dependencies unless a measured requirement justifies them.
- Preserve existing algorithm behavior and routes.
- Maintain API documentation at `/api/docs` and `/api/redoc`.

### Business and correctness rules

- The heuristic is the only comparison variable.
- Four-way movement currently has unit edge cost; heuristic suitability must be described in that context.
- A completed trace is immutable in the UI while other traces continue.
- Metrics shown in the UI must originate in the event/result payload.
- Execution failure and no-path states must be distinguishable from a still-running trace.

### Edge cases

- Start equals goal.
- Blocked start or goal.
- No path for the shared obstacle layout.
- Empty or very small valid grids at the schema bounds.
- Dense but valid obstacles.
- Invalid coordinate format, out-of-bounds points, duplicate heuristics, unsupported movement model, or unsupported heuristic.
- Empty event list or malformed comparison payload.
- Replacing a comparison while playback is active.
- Pause/restart/finish at step zero and at the terminal step.
- Mobile widths where four panels cannot remain side by side.

## 4. Technical Change Overview

Risk scores use the requested seven dimensions, each scored 1–3: scope, dependencies, blocking factor, stability, UX impact, testing complexity, and reversibility. A total of 7–11 is Low, 12–16 Medium, and 17–21 High.

| Component | Type | Description | Risk score | Dependencies |
|---|---|---|---:|---|
| `backend/app/algorithms/astar_grid.py` | Enhancement | Keep one configurable A* engine authoritative for the four heuristic functions; harden metadata and movement-model explanations. | 12 / Medium | Existing event contract and Pydantic config |
| `backend/app/algorithms/heuristic_comparison.py` | Enhancement | Preserve one shared problem, compact summaries, nested traces, terminal status, and deterministic comparison metadata. | 14 / Medium | A* engine, registry, API serializer |
| `backend/app/algorithms/base.py` | Enhancement | Confirm replay event fields support all visualizer states without redundant payload growth. | 13 / Medium | Every algorithm engine and frontend replay consumer |
| `backend/app/algorithms/registry.py` | Enhancement | Keep comparison metadata discoverable and aligned with frontend visualization routing. | 8 / Low | Existing registry metadata |
| `backend/app/main.py` / `backend/app/schemas.py` | Enhancement | Document and validate comparison execution payloads; retain current synchronous response contract. | 11 / Low | FastAPI/Pydantic models |
| `backend/tests/test_heuristic_comparison_flagship.py` | Test | Expand correctness, determinism, metrics, invalid input, edge-case, and event-contract coverage. | 10 / Low | Existing pytest setup |
| `frontend/src/hooks/useAnimationController.ts` | Refactor | Make the controller the shared playback authority and verify generation/timer lifecycle semantics. | 16 / Medium | Generic visualizer and comparison consumers |
| `frontend/src/pages/VisualizerPage.tsx` | Refactor | Replace the separate fixed `setInterval` replay with the shared controller while preserving generic visualizer behavior. | 16 / Medium | Controller API, existing visualizer event model |
| `frontend/src/features/heuristic-comparison/*` | Enhancement | Add robust panel states, analytics, shared legend, synchronization details, dark-mode tokens, and accessible control/status semantics. | 17 / High | Comparison API payload and controller |
| `frontend/src/components/GridVisualizer.tsx` / `ExecutionTimeline.tsx` | Enhancement | Reuse consistent state rendering and keyboard/ARIA semantics across visualizers. | 14 / Medium | Global tokens and event contract |
| `frontend/src/index.css` and feature CSS | Enhancement | Consolidate semantic tokens and responsive rules; remove feature-level color drift. | 13 / Medium | Existing layout and dark-mode classes |
| `frontend/src/pages/AlgorithmsPage.tsx` / `AlgorithmDetailPage.tsx` / `Layout.tsx` | Enhancement | Improve grouped discovery and connect A* detail/navigation to the flagship analysis. | 10 / Low | Registry metadata and existing routes |
| `frontend/e2e/platform.spec.ts` | Test | Cover actual playback progression, pause/resume, speed timing, fast-forward, restart, finish, synchronization, metrics, and mobile layout. | 15 / Medium | Running backend/Vite services |
| `frontend` test tooling | Decision / possible addition | Prefer existing Playwright and TypeScript checks first; introduce a focused unit runner only if controller extraction cannot be meaningfully tested otherwise. | 12 / Medium | Dependency review and coverage target |
| `docs/architecture/*`, `docs/api/*`, `docs/development/*` | Documentation | Record comparison payload shape, event semantics, extension rules, and shared animation lifecycle. | 8 / Low | Final implementation contracts |

### Recommended delivery work packages

| Work package | Outcome | Primary files |
|---|---|---|
| W1 — Contract hardening | Stable schemas, event semantics, formula suitability metadata, and shared-problem signature. | Backend algorithm/base/schema modules |
| W2 — Comparison validation | Full backend edge-case and consistency suite. | `backend/tests/` |
| W3 — Shared playback | One controller contract used by comparison and ordinary visualizer. | `useAnimationController.ts`, `VisualizerPage.tsx` |
| W4 — Comparison analytics | Real chart data, metrics table highlights, and deterministic explanation. | Heuristic comparison feature |
| W5 — UI system consistency | Shared state legend, tokens, dark mode, responsive grid/panel rules, and detail/discovery links. | `index.css`, components, pages, feature CSS |
| W6 — Browser verification | Behavior-first E2E coverage across playback and responsive states. | `frontend/e2e/platform.spec.ts` |
| W7 — Documentation and release checks | Updated architecture/API docs and full required checks. | `docs/`, build/test scripts |

## 5. Impact Analysis

### Codebase impact

**Backend**

- `astar_grid.py` remains the single search implementation and source of heuristic metadata.
- `heuristic_comparison.py` remains the orchestration boundary. The current implementation runs the shared variants sequentially on the backend and packages each replay trace; the frontend provides the synchronized learner-facing timeline.
- `registry.py` and `main.py` remain the discovery and execution boundaries.
- Tests extend existing direct-engine and FastAPI `TestClient` patterns.

**Frontend**

- The feature-scoped comparison page remains the flagship experience.
- `useAnimationController.ts` becomes the common playback primitive instead of being used only by the comparison page.
- `VisualizerPage.tsx` is the main integration risk because it currently owns a separate fixed-interval loop.
- `GridVisualizer`, `ExecutionTimeline`, `MetricsPanel`, and global CSS are the reuse points for consistency rather than creating parallel primitives.
- Existing routing remains explicit in `App.tsx`; no route replacement is required.

### Data model and persistence

No database migration is required. Executions remain process-local and synchronous. The comparison payload should continue to carry a problem signature, shared problem metadata, compact summaries, and event traces. If payload size becomes a measured problem, the next design step is a versioned replay payload or server-side trace storage; it is not part of this epic.

### API changes

The existing `POST /api/v1/executions` endpoint already accepts the registered comparison ID and returns replayable events. Planned changes should be backward-compatible:

- Preserve `algorithm_id = "astar-heuristic-comparison"`.
- Preserve the four heuristic identifiers and existing summary field names.
- Clarify OpenAPI descriptions for shared-problem guarantees, movement model, units, and nested run traces.
- Add validation only through the existing registry-selected Pydantic config model.
- Keep 404 for unknown algorithms/executions, 422 for invalid configuration, and 400 for invalid export format.

### UI/UX changes

- Extend the existing comparison workspace rather than creating a second comparison architecture.
- Add chart/analytics sections below the synchronized grids.
- Make current step, per-run step, completion, and pinned terminal state obvious.
- Align comparison feature colors with semantic tokens and support dark mode.
- Apply playback semantics to the generic visualizer.
- Improve keyboard and screen-reader communication without making the grid visually noisy.

### Migration strategy

1. Preserve the current comparison API and route.
2. Introduce shared playback behind the current UI contract.
3. Migrate ordinary visualizer playback one page at a time, keeping the old behavior covered until the replacement passes E2E.
4. Add analytics from existing trace data without changing algorithm outputs.
5. Update documentation after the API and controller contracts stabilize.

### Rollback plan

- Revert frontend controller integration while retaining the tested comparison feature if ordinary visualizer migration regresses.
- Revert analytics and CSS changes independently because they consume existing payloads.
- Revert backend metadata additions independently as long as stable existing fields remain.
- Do not perform destructive data migrations; rollback is code-level and route-compatible.

### Tradeoffs

- Synchronous full-trace responses keep the existing architecture simple and deterministic but limit very large grids. The epic keeps current schema bounds rather than adding streaming infrastructure.
- A shared global timeline makes the comparison easy to understand and deterministic, but it does not claim that backend variants execute in physical lockstep. Each panel is derived from its own real trace at the same replay cursor.
- CSS/SVG analytics avoid a new chart dependency and are adequate for the current metric set; a chart library can be reconsidered only after a requirement for richer interaction is demonstrated.
- The existing DM Sans/DM Mono design direction is retained instead of adding duplicate fonts.

## 6. Testing Strategy

### Unit and engine tests

Extend the current pytest modules with focused cases for:

- Formula output for all identifiers and the four-way movement model.
- One exact shared problem signature across every run.
- Same seed and config producing structurally equal traces after removing wall-clock runtime.
- Different seeds changing generated obstacles while preserving the same problem within a comparison.
- All four heuristics returning valid paths and equal optimal unit-cost path cost when reachable.
- Zero heuristic exposing `h = 0` and Dijkstra/uniform-cost metadata.
- Expanded/discovered/frontier/explored/path/steps/event-count consistency.
- Start equals goal, blocked endpoints, no path, dense obstacles, small bounds, and invalid configuration.
- Event ordering and terminal `COMPLETED`/`FAILED` semantics.

### Integration/API tests

- `GET /api/v1/algorithms` includes the comparison metadata.
- `POST /api/v1/executions` returns the comparison event contract and all four runs.
- Invalid algorithm, malformed config, unsupported heuristic, and invalid movement model return expected HTTP status codes.
- `/api/docs` exposes the intended execution endpoint and descriptions.

### Frontend behavior tests

Because the repository currently has no Vitest/Jest/Testing Library setup, first use the existing TypeScript and Playwright checks for user-visible behavior. If the controller is extracted into pure transition logic, add a minimal focused unit runner only if it materially improves branch coverage without duplicating E2E assertions.

Required browser assertions:

- Four named panels render only after a real comparison response.
- Shared problem signature/start/goal/obstacle count are consistent.
- Progress starts at zero, advances after resume/play, stops while paused, and resumes.
- Speed selection changes measured inter-step timing within a tolerance.
- Fast Forward advances faster but does not jump directly to final state.
- Finish reaches the terminal frame; Restart returns to step zero and clears playback state.
- Each panel stays pinned after its own trace completes while other panels continue.
- Final table values match visible run data and are not placeholder values.
- No-path and API error states are announced and visually distinguishable.
- Keyboard focus and reduced-motion behavior work.
- Desktop, tablet, and mobile layouts remain readable without horizontal page overflow.

### Coverage goals

- Aim for at least 90% branch coverage over new backend comparison logic and any extracted controller transition logic.
- Keep existing regression suites green; do not lower coverage or remove tests to accommodate implementation.
- Treat wall-clock execution time as a non-deterministic field and assert non-negativity/shape rather than exact values.

## 7. User Behavior Testing

### Critical E2E scenarios

| ID | Journey | Expected result |
|---|---|---|
| E1 | Open A* detail/library and launch heuristic analysis | Route is discoverable and opens the comparison workspace. |
| E2 | Run default comparison | Four panels, formulas, shared problem, and real metrics appear. |
| E3 | Pause and resume | Cursor stops while paused and continues from the same index. |
| E4 | Change speed | Subsequent advancement interval changes according to selected bounded speed. |
| E5 | Fast-forward | Playback accelerates and remains replayable before completion. |
| E6 | Step through events | Forward/backward controls move one event and pause playback. |
| E7 | Restart | Cursor returns to zero; no old timer advances the new state. |
| E8 | Finish and mixed trace lengths | All panels show their terminal state; earlier-finishing runs remain pinned. |
| E9 | Compare a no-path input | All runs report no route without fabricated path metrics. |
| E10 | Use mobile viewport | Panels stack, controls remain reachable, and no critical content clips. |
| E11 | Use keyboard and reduced motion | Focus is visible; shortcuts do not affect text inputs; motion is reduced without disabling functionality. |
| E12 | Existing ordinary visualizer | Existing algorithm route still runs and playback behavior remains valid after controller migration. |

### Acceptance test cases

1. Given one seeded four-way grid, when the comparison runs, then every run reports the same problem signature, endpoints, obstacle set, movement model, and cost model.
2. Given a reachable unit-cost problem, when all variants complete, then path costs are optimal and metrics are sourced from actual traces.
3. Given a paused comparison, when Step Forward is selected, then exactly one global replay position advances and the comparison remains paused.
4. Given a running comparison, when Restart is selected, then no callback from the prior generation changes the new index.
5. Given different trace lengths, when the longest trace continues, then completed panels preserve their terminal frames and completion labels.
6. Given an invalid configuration, when Run comparison is selected, then an accessible error is shown and no stale execution is presented as current.

### Regression flows

- Landing page, library search/grouping, algorithm detail, generic visualizer, existing `/comparison` A* vs Greedy flow, dark mode, mobile navigation, API health, and all existing registered algorithms.

## 8. Implementation Notes

### Patterns to follow

- Use the registry in `backend/app/algorithms/registry.py` for metadata, config models, factories, and visualization type.
- Use `AlgorithmEngine`, `AlgorithmEvent`, and `AlgorithmResult` from `backend/app/algorithms/base.py`; do not create a second event protocol.
- Keep A* search logic in `AStarGridEngine`; comparison orchestration should configure and invoke that engine rather than copy its loop.
- Keep Pydantic V2 validation (`field_validator`, `model_validator`, typed fields) and FastAPI's existing endpoint error mapping.
- Treat backend event logs as authoritative; the frontend derives visual frames from events and does not recompute the algorithm.
- Prefer local React state and feature-scoped modules consistent with the current application. Introduce shared context/store only if profiling or state coordination demonstrates a need.
- Reuse `GridVisualizer`, `ExecutionTimeline`, `MetricsPanel`, and global CSS tokens before adding new primitives.
- Keep the controller single-timer/generation-guard pattern from `useAnimationController.ts`, then make it the ordinary visualizer's source of truth.

### Architecture decisions

#### AD-1: One A* implementation, configurable heuristic

The existing `AStarGridEngine` accepts a validated heuristic identifier. The comparison engine creates four configs from one materialized grid and invokes the same engine. This preserves behavior and makes heuristic selection the only algorithmic variable.

#### AD-2: Shared problem is materialized before variant runs

`HeuristicComparisonEngine._shared_grid()` generates or normalizes obstacles once. The problem metadata includes a stable hash signature derived from grid dimensions, endpoints, obstacles, density, movement model, and seed. Every run embeds that metadata for API and UI verification.

#### AD-3: Event replay is the frontend boundary

The backend returns snapshots containing current node, frontier, explored set, path, metrics, and metadata. The frontend must render those snapshots directly. New event fields should be added only when an existing field cannot express a needed state.

#### AD-4: Global comparison cursor, independent run state

The comparison controller owns one replay index. `eventAt()` selects each run's event at that index and pins completed shorter traces to their last event. This is synchronized presentation of independent real traces, not a fabricated lockstep algorithm.

#### AD-5: Lightweight analytics

Use semantic HTML, CSS bars, or inline SVG derived from the trace summaries and progress series. Do not add a chart dependency merely to render two static metric views.

### Technical debt and follow-up

- The generic `VisualizerPage.tsx` still has a separate fixed `setInterval`; this is the largest animation consistency debt.
- The comparison page currently contains feature-local color constants and fallback formula text; these should consume shared semantic tokens/metadata.
- The backend returns complete nested traces synchronously. Very large execution payloads may require a future transport/storage design.
- There is no frontend unit-test harness. The project should decide whether controller transition extraction justifies one before adding a dependency.
- Runtime metrics are wall-clock measurements and are useful for observation, not strict deterministic regression assertions.

### Security and data protection

- No authentication or user data persistence is currently present; do not introduce credentials or secrets into the comparison payload.
- Validate all user-controlled grid coordinates, obstacle values, heuristic names, and numeric bounds through Pydantic models.
- Keep CORS behavior unchanged unless a documented deployment target requires a new origin.
- Do not render event explanations or metadata as unsanitized HTML.
- Avoid logging full potentially large traces in production diagnostics.

## 9. Acceptance Criteria

### A* comparison

- [ ] `manhattan`, `euclidean`, `chebyshev`, and `zero` are validated stable identifiers.
- [ ] One shared materialized grid is used for every run, with identical endpoints, obstacles, movement model, cost model, and seed metadata.
- [ ] The comparison uses the existing configurable A* engine, with no duplicated search implementation.
- [ ] All required metrics are real, internally consistent, and exposed in the API and UI.
- [ ] Four panels render and remain usable at desktop, tablet, and mobile widths.
- [ ] Per-panel completion and mixed trace lengths are represented correctly.
- [ ] Comparison table and charts derive from actual execution data.
- [ ] Educational explanation is deterministic and consistent with the movement/cost model.

### Animation

- [ ] Play, pause, resume, restart, step forward, supported backward step, speed, fast-forward, finish, and progress behave correctly.
- [ ] Speed changes actual timing and fast-forward is distinct from finish.
- [ ] There is exactly one active loop per execution/controller.
- [ ] Restart, replacement execution, unmount, and completion invalidate stale callbacks.
- [ ] Ordinary visualizer playback uses the shared controller or has a documented event-model exception.
- [ ] Reduced-motion mode preserves functionality while minimizing transitions.

### Frontend

- [ ] Semantic design tokens and state legend are shared across visualizers.
- [ ] Dark mode, focus states, accessible names, live status/error behavior, and keyboard controls are covered.
- [ ] Algorithm library/detail navigation makes the flagship comparison discoverable.
- [ ] No new control is decorative or non-functional.
- [ ] No horizontal overflow or clipped critical controls exists at supported mobile widths.

### Engineering

- [ ] Backend tests pass, including new comparison edge cases.
- [ ] `npm run build` passes with no TypeScript errors.
- [ ] Existing and new Playwright tests pass.
- [ ] API docs reflect the comparison execution contract.
- [ ] New backend/controller branches meet the agreed coverage target or the gap is explicitly recorded.
- [ ] Existing algorithm behavior and unrelated user flows remain green.

## 10. Open Questions & Risks

### Blockers

None for local planning. Jira issue linkage, project ownership, and Confluence publication are unavailable because the user asked to skip them.

### Unknowns requiring an implementation decision

1. Should frontend unit testing remain Playwright-only, or should the controller transition logic be extracted and covered with a small unit-test runner?
2. Should the chart views be CSS/inline SVG only, or is there an existing charting dependency not currently visible in `frontend/package.json` that should be reused?
3. Should “execution time” remain backend wall-clock time, or should the UI also expose client replay duration as a separate metric? They must not be conflated.
4. Is four-way unit-cost movement the permanent supported model for this comparison, or should a future epic add explicit diagonal/terrain cost semantics before making heuristic suitability broader?
5. What production grid-size limit is acceptable if synchronous full-trace responses remain the transport?

### Assumptions

- The current repository is the source of truth for architecture and existing behavior.
- The supplied requirements describe one epic, not a request to rewrite the project.
- No database, auth, deployment, or multi-user persistence work is required.
- Existing uncommitted change in `frontend/e2e/platform.spec.ts` is intentional and must be preserved.
- Current backend test results and build/E2E results from the preceding work session are valid baselines, but must be rerun after any implementation changes.

### Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Generic and comparison playback diverge | Confusing controls and race regressions | Migrate generic playback to the shared controller and test timer invalidation. |
| Full nested traces grow too large | Slow API responses and browser memory use | Keep schema bounds, measure payloads, avoid redundant event fields, defer streaming until evidence. |
| Runtime metrics make deterministic tests flaky | False failures | Strip timing from structural equality tests; assert type/range and display units. |
| Heuristic claims overgeneralize | Misleading education | Derive explanation from movement/cost metadata and avoid universal admissibility claims. |
| Feature CSS bypasses tokens | Dark-mode and state-color inconsistency | Centralize semantic variables and add visual/accessibility checks. |
| E2E timing assumptions become flaky | Intermittent CI failures | Use condition-based assertions, bounded timeouts, and state transitions instead of fixed sleeps. |
| New charts increase dependency surface | More maintenance and bundle size | Start with CSS/SVG and reuse existing data structures. |

## 11. Codebase Analysis

### Affected modules

- `backend/app/algorithms/astar_grid.py` — configurable A* engine, grid config, heuristic definitions, deterministic obstacles, snapshots, and canonical metrics.
- `backend/app/algorithms/heuristic_comparison.py` — shared-problem orchestration, nested traces, summaries, problem signature, and comparison terminal event.
- `backend/app/algorithms/base.py` — generic replayable event/result contract.
- `backend/app/algorithms/registry.py` — algorithm metadata and engine/config registration.
- `backend/app/main.py` — FastAPI routes, config preparation, synchronous execution, in-memory result retrieval, and export.
- `backend/app/schemas.py` — execution/comparison request and response envelopes.
- `backend/tests/test_heuristic_comparison_flagship.py` — flagship engine correctness and edge cases.
- `backend/tests/test_search_additions.py` — search/comparison additions and summaries.
- `backend/tests/test_extended_registry.py` — registry/API shared-grid checks.
- `frontend/src/features/heuristic-comparison/HeuristicComparisonPage.tsx` — flagship UI, controls, panel replay, metrics, and explanation.
- `frontend/src/features/heuristic-comparison/models.ts` — comparison payload normalization and trace selection.
- `frontend/src/features/heuristic-comparison/heuristic-comparison.css` — feature layout and panel styling.
- `frontend/src/hooks/useAnimationController.ts` — reusable playback controller.
- `frontend/src/pages/VisualizerPage.tsx` — generic visualizer playback migration target.
- `frontend/src/components/GridVisualizer.tsx`, `ExecutionTimeline.tsx`, `MetricsPanel.tsx`, `AlgorithmStateVisualizer.tsx` — reusable visualization primitives.
- `frontend/src/index.css` — global design tokens, responsive rules, dark mode, and generic visualizer styles.
- `frontend/src/App.tsx`, `AlgorithmsPage.tsx`, `AlgorithmDetailPage.tsx`, `Layout.tsx` — routes and discovery/navigation surfaces.
- `frontend/e2e/platform.spec.ts` — existing behavior-oriented browser coverage.
- `docs/architecture/overview.md`, `docs/api/endpoints.md`, `docs/development/adding-algorithms.md` — architecture, API, and extension documentation.

### Patterns discovered

**API:** FastAPI app-level routes under `/api/v1`, registry-selected Pydantic config validation, synchronous event traces, process-local result dictionaries, explicit HTTP exceptions, and OpenAPI at `/api/docs`.

**Backend algorithms:** Generic `AlgorithmEngine` produces `AlgorithmEvent` snapshots and `AlgorithmResult`; A* uses deterministic config and structured metrics; comparison wraps the same engine rather than duplicating search logic.

**Components:** `*Page.tsx` page naming, reusable components under `frontend/src/components`, feature-local modules under `frontend/src/features`, and explicit routes in `App.tsx`.

**State:** Local React hooks; backend event logs are authoritative; comparison derives all four frames from one controller index.

**Styling:** Global CSS tokens use DM Sans/DM Mono, teal semantic accent, state colors, dark-mode variables, responsive breakpoints at approximately 900px/640px, and `:focus-visible`.

**Testing:** Backend pytest with direct engine tests and `TestClient`; Playwright Chromium E2E with Vite/Uvicorn web servers; no frontend unit-test framework currently configured.

### Reference implementations

- `backend/app/algorithms/astar_grid.py` — event-producing grid search and canonical metrics.
- `backend/app/algorithms/heuristic_comparison.py` — current shared-problem comparison pattern.
- `backend/app/algorithms/base.py` — common event/result abstraction.
- `frontend/src/hooks/useAnimationController.ts` — single-timer, generation-guarded replay.
- `frontend/src/features/heuristic-comparison/models.ts` — variable-length trace normalization.
- `frontend/src/components/ExecutionTimeline.tsx` — timeline presentation.
- `frontend/src/components/GridVisualizer.tsx` — generic grid rendering and legend patterns.
- `frontend/src/pages/AlgorithmsPage.tsx` — registry-driven algorithm grouping/search/discovery.
- `frontend/src/pages/AlgorithmDetailPage.tsx` — detail-page metadata, explanation, and related algorithm links.
- `docs/development/adding-algorithms.md` — extension workflow.

### Test locations and conventions

- Backend: `backend/tests/`, configured by `backend/pyproject.toml`; eight modules and 30 existing tests at discovery time.
- Frontend E2E: `frontend/e2e/platform.spec.ts`; `frontend/playwright.config.ts` starts Vite and Uvicorn and runs Chromium.
- Frontend build/type: `frontend/package.json` uses `tsc -b && vite build`.
- Existing flagship E2E covers four headings, initial progress, resume progression, pause, fast-forward, and restart.
- Existing worktree modification: `frontend/e2e/platform.spec.ts`; preserve and rerun it.

### Baseline checks observed before this planning artifact

The preceding work session recorded the following repository checks:

- Backend: **30 passed**.
- Frontend build: **PASS**.
- Full E2E suite: **4 passed**.
- Repeated A* comparison test: **3/3 passed**.

These are baseline observations, not new checks performed while writing this document. Any implementation work must rerun the commands in Section 9.

## 12. Linked Tickets

No Jira epic key or linked tickets were supplied. Jira retrieval and Confluence publication were skipped at the user's direction.

| Key | Summary | Type | Story points |
|---|---|---|---:|
| Local-W1 | Harden A* comparison contract and metrics | Work package | TBD |
| Local-W2 | Expand backend correctness and API tests | Work package | TBD |
| Local-W3 | Migrate ordinary visualizer to shared animation controller | Work package | TBD |
| Local-W4 | Add comparison analytics and educational readout | Work package | TBD |
| Local-W5 | Consolidate frontend design/accessibility/responsive behavior | Work package | TBD |
| Local-W6 | Expand Playwright behavior and viewport coverage | Work package | TBD |
| Local-W7 | Update architecture/API/developer documentation and release checks | Work package | TBD |

## Proposed Implementation Order

1. **Audit and contract freeze** — confirm current event/result payloads, shared-problem signature, movement-model limits, and controller behavior.
2. **Backend hardening** — finish schema descriptions, event semantics, metric consistency, and edge-case coverage without duplicating A* logic.
3. **Shared playback migration** — extract or adapt the controller contract, replace the generic visualizer's fixed interval, and verify stale timer invalidation.
4. **Comparison analytics** — add real expanded-node/frontier/progress views, table highlights, and model-aware deterministic explanation.
5. **Design-system alignment** — move feature CSS to semantic tokens, unify legends/states, improve dark mode and panel readability.
6. **Discovery/detail refinement** — ensure the A* comparison is grouped, linked, and described through existing registry-driven pages.
7. **Accessibility/responsive pass** — verify keyboard behavior, live status, focus, reduced motion, and mobile stacking.
8. **Verification and documentation** — run backend tests, frontend build, E2E suite, repeated comparison test, and update architecture/API docs.

## Review and Publication Status

This document is saved locally for review at:

`docs/planning/ai-algorithm-visualiser-feature-expansion.md`

It has not been published to Confluence. The next workflow step, if desired, is to turn the local work packages into an implementation plan and tickets rather than relying on a Jira-linked overview URL.

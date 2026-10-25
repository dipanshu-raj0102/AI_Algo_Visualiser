import { FastForward, Pause, Play, RotateCcw, SkipBack, SkipForward, Sparkles } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { createExecution } from "../../api";
import { useAnimationController, ANIMATION_SPEEDS, type AnimationSpeed } from "../../hooks/useAnimationController";
import {
  displayHeuristic,
  eventAt,
  HEURISTIC_ORDER,
  parseComparisonExecution,
  type ComparisonEvent,
  type ComparisonProblem,
  type ComparisonRun,
  type HeuristicName,
} from "./models";
import "./heuristic-comparison.css";

type GridConfig = {
  rows: number;
  cols: number;
  start: string;
  goal: string;
  obstacle_density: number;
  seed: number;
};

const DEFAULT_GRID: GridConfig = {
  rows: 14,
  cols: 22,
  start: "1,1",
  goal: "12,20",
  obstacle_density: 0.18,
  seed: 482193,
};

const FORMULA_FALLBACK: Record<HeuristicName, { formula: string; description: string }> = {
  manhattan: { formula: "|dr| + |dc|", description: "Sum of orthogonal distance to the goal." },
  euclidean: { formula: "sqrt(dr² + dc²)", description: "Straight-line distance to the goal." },
  chebyshev: { formula: "max(|dr|, |dc|)", description: "Maximum coordinate distance to the goal." },
  zero: { formula: "0", description: "No heuristic; A* becomes Dijkstra / uniform-cost search." },
};

const COLORS: Record<HeuristicName, string> = {
  manhattan: "#0f766e",
  euclidean: "#2563eb",
  chebyshev: "#9333ea",
  zero: "#c2410c",
};

function formatMetric(value: number | null | undefined, suffix = ""): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return `${Number.isInteger(value) ? value : value.toFixed(2)}${suffix}`;
}

function metricValue(event: ComparisonEvent | undefined, name: string, fallback: number): number {
  const value = event?.metrics[name];
  return typeof value === "number" ? value : fallback;
}

function comparisonInsight(runs: ComparisonRun[]): string {
  const reached = runs.filter((run) => run.reached && run.path_cost !== null);
  if (!reached.length) return "None of the four searches reached the goal on this shared obstacle layout.";
  const bestCost = Math.min(...reached.map((run) => run.path_cost ?? Number.POSITIVE_INFINITY));
  const shortest = reached.filter((run) => run.path_cost === bestCost);
  const bestExpanded = Math.min(...shortest.map((run) => run.expanded));
  const winner = shortest.find((run) => run.expanded === bestExpanded) ?? shortest[0];
  const leastWork = reached.reduce((best, run) => run.expanded < best.expanded ? run : best, reached[0]);
  if (winner.heuristic === leastWork.heuristic) {
    return `${displayHeuristic(winner.heuristic)} found the shortest route (${formatMetric(winner.path_cost)} cost) while expanding the fewest cells (${formatMetric(winner.expanded)}). On this seeded grid, its estimate focused the search without sacrificing optimality.`;
  }
  return `${displayHeuristic(winner.heuristic)} and ${displayHeuristic(leastWork.heuristic)} both reached the same shortest route (${formatMetric(winner.path_cost)} cost). ${displayHeuristic(leastWork.heuristic)} expanded fewer cells (${formatMetric(leastWork.expanded)} vs ${formatMetric(winner.expanded)}), so it was the more efficient search for this particular obstacle layout.`;
}

export function ComparisonGrid({ run, event, problem }: { run: ComparisonRun; event: ComparisonEvent | undefined; problem: ComparisonProblem }) {
  const obstacles = new Set(problem.obstacles);
  const explored = new Set(event?.explored ?? []);
  const frontier = new Set((event?.frontier ?? []).map((item) => item.node));
  const path = new Set(event?.path ?? []);
  const cells = Array.from({ length: problem.rows * problem.cols }, (_, index) => {
    const node = `${Math.floor(index / problem.cols)},${index % problem.cols}`;
    const state = node === problem.start ? "start" : node === problem.goal ? "goal" : node === event?.current_node ? "current" : path.has(node) ? "path" : obstacles.has(node) ? "obstacle" : frontier.has(node) ? "frontier" : explored.has(node) ? "explored" : "";
    return { node, state };
  });
  return <div className="hcx-grid" style={{ gridTemplateColumns: `repeat(${problem.cols}, minmax(0, 1fr))` }} role="grid" aria-label={`${displayHeuristic(run.heuristic)} search grid at step ${event?.iteration ?? 0}`}>
    {cells.map(({ node, state }) => <div key={node} className={`hcx-cell ${state}`} role="gridcell" aria-label={`${node}${state ? `, ${state}` : " empty"}`} title={`${node}${state ? ` · ${state}` : ""}`} />)}
  </div>;
}

export function HeuristicPanel({ run, event, problem, isComplete }: { run: ComparisonRun; event: ComparisonEvent | undefined; problem: ComparisonProblem; isComplete: boolean }) {
  const formula = run.heuristic_formula || FORMULA_FALLBACK[run.heuristic].formula;
  const description = run.heuristic_description || FORMULA_FALLBACK[run.heuristic].description;
  const expanded = metricValue(event, "expanded", run.expanded);
  const frontier = event?.frontier.length ?? 0;
  return <article className="hcx-panel" style={{ ["--hcx-accent" as string]: COLORS[run.heuristic] }} aria-label={`${displayHeuristic(run.heuristic)} heuristic panel`}>
    <header className="hcx-panel-header">
      <div><span className="hcx-panel-kicker">{isComplete ? "TRACE COMPLETE" : "LIVE TRACE"}</span><h3>{displayHeuristic(run.heuristic)}</h3></div>
      <span className={`hcx-status ${run.reached ? "reached" : "pending"}`}>{isComplete ? (run.reached ? "Reached" : "Stopped") : "Running"}</span>
    </header>
    <div className="hcx-formula"><strong>{formula}</strong><span>{description}</span></div>
    <div className="hcx-grid-stage"><ComparisonGrid run={run} event={event} problem={problem} /></div>
    <div className="hcx-panel-footer"><span className="mono">step {event ? event.iteration : 0} · {event?.event_type.replaceAll("_", " ") ?? "waiting"}</span><span className="mono">{event?.current_node ?? problem.goal}</span></div>
    <div className="hcx-panel-metrics" aria-label={`${displayHeuristic(run.heuristic)} live metrics`}>
      <div><span>Expanded</span><b>{formatMetric(expanded)}</b></div>
      <div><span>Frontier</span><b>{formatMetric(frontier)}</b></div>
      <div><span>Route</span><b>{formatMetric(run.path_cost)}</b></div>
    </div>
  </article>;
}

export function HeuristicComparisonPage() {
  const [grid, setGrid] = useState<GridConfig>(DEFAULT_GRID);
  const [execution, setExecution] = useState<ReturnType<typeof parseComparisonExecution>>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const runs = execution?.runs ?? [];
  const timeline = useMemo(() => Array.from({ length: Math.max(0, ...runs.map((run) => run.events.length)) }, (_, index) => index), [runs]);
  const controller = useAnimationController(timeline, { baseDelayMs: 380 });

  useEffect(() => {
    controller.restart();
  }, [execution, controller.restart]);

  const runComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await createExecution("astar-heuristic-comparison", { grid, heuristics: HEURISTIC_ORDER });
      const parsed = parseComparisonExecution(response);
      if (!parsed) throw new Error("The backend returned no heuristic traces.");
      setExecution(parsed);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to run heuristic comparison");
    } finally {
      setLoading(false);
    }
  };

  const problem = execution?.problem ?? { rows: grid.rows, cols: grid.cols, start: grid.start, goal: grid.goal, obstacles: [] };
  const allComplete = runs.length > 0 && controller.isComplete;
  const updateNumber = (key: "rows" | "cols" | "seed", value: string) => setGrid((current) => ({ ...current, [key]: Math.max(0, Number(value)) }));

  return <main className="hcx-page page-width page-top">
    <header className="hcx-hero">
      <div>
        <span className="eyebrow"><Sparkles size={13} /> FLAGSHIP EXPERIMENT · A* HEURISTIC IMPACT</span>
        <h1>Same map. Four ways to estimate the future.</h1>
        <p>Watch Manhattan, Euclidean, Chebyshev, and zero heuristic search the exact same seeded grid. The only variable is the estimate guiding each frontier.</p>
      </div>
      <div className="hcx-hero-note"><span className="hcx-note-label">COMPARISON GUARANTEE</span><strong>One materialized problem</strong><span>Every panel uses the backend’s shared obstacles, start, goal, and movement model.</span></div>
    </header>

    <section className="hcx-toolbar" aria-label="Comparison configuration">
      <div className="hcx-toolbar-fields">
        <label>Rows<input type="number" min={4} max={40} value={grid.rows} onChange={(event) => updateNumber("rows", event.target.value)} /></label>
        <label>Columns<input type="number" min={4} max={60} value={grid.cols} onChange={(event) => updateNumber("cols", event.target.value)} /></label>
        <label>Start<input value={grid.start} onChange={(event) => setGrid((current) => ({ ...current, start: event.target.value }))} /></label>
        <label>Goal<input value={grid.goal} onChange={(event) => setGrid((current) => ({ ...current, goal: event.target.value }))} /></label>
        <label>Density <span>{Math.round(grid.obstacle_density * 100)}%</span><input type="range" min="0" max="0.45" step="0.01" value={grid.obstacle_density} onChange={(event) => setGrid((current) => ({ ...current, obstacle_density: Number(event.target.value) }))} /></label>
        <label>Seed<input type="number" min={0} value={grid.seed} onChange={(event) => updateNumber("seed", event.target.value)} /></label>
      </div>
      <button className="button button-dark" onClick={runComparison} disabled={loading}>{loading ? "Running four traces…" : "Run comparison"}<Play size={14} fill="currentColor" /></button>
    </section>
    {error && <div className="hcx-error" role="alert">{error}</div>}

    {runs.length > 0 ? <>
      <section className="hcx-playback" aria-label="Comparison playback controls">
        <div className="hcx-playback-actions">
          <button className="icon-button" onClick={controller.restart} aria-label="Restart comparison"><RotateCcw size={16} /></button>
          <button className="icon-button" onClick={controller.stepBackward} aria-label="Step backward"><SkipBack size={16} /></button>
          <button className="hcx-play-button" onClick={controller.isPlaying ? controller.pause : controller.resume} aria-label={controller.isPlaying ? "Pause comparison" : "Resume comparison"} disabled={allComplete}>{controller.isPlaying ? <Pause size={16} /> : <Play size={16} fill="currentColor" />}</button>
          <button className="icon-button" onClick={controller.stepForward} aria-label="Step forward"><SkipForward size={16} /></button>
          <button className="icon-button" onClick={controller.fastForward} aria-label="Fast-forward comparison" title="Fast-forward (8×)"><FastForward size={16} /></button>
          <button className="hcx-finish-button" onClick={controller.finish} disabled={allComplete}>Finish</button>
        </div>
        <div className="hcx-progress-wrap"><div className="hcx-progress" aria-label={`Comparison progress ${Math.round(controller.progress)} percent`} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(controller.progress)}><span style={{ width: `${controller.progress}%` }} /></div><span className="mono">{controller.count ? `${controller.index + 1} / ${controller.count}` : "0 / 0"}</span></div>
        <label className="hcx-speed">Speed<select aria-label="Playback speed" value={controller.speed} onChange={(event) => controller.setSpeed(Number(event.target.value) as AnimationSpeed)}>{ANIMATION_SPEEDS.map((speed) => <option key={speed} value={speed}>{speed}×</option>)}</select></label>
      </section>

      <section className="hcx-shared-problem"><div><span className="hcx-section-label">SHARED PROBLEM</span><strong>{problem.rows} × {problem.cols} grid</strong><span>Start {problem.start} · Goal {problem.goal} · {problem.obstacles.length} obstacles · seed {problem.seed ?? grid.seed}</span></div><span className="hcx-signature mono">{problem.signature ? `ID ${problem.signature}` : "4-way movement"}</span></section>

      <section className="hcx-panel-grid">{runs.map((run) => <HeuristicPanel key={run.heuristic} run={run} event={eventAt(run, controller.index)} problem={problem} isComplete={controller.index >= run.events.length - 1} />)}</section>

      <section className="hcx-insight"><div><span className="hcx-section-label">DETERMINISTIC READOUT</span><h2>What changed when the estimate changed?</h2><p>{comparisonInsight(runs)}</p></div><div className="hcx-insight-stat"><span>Current shared step</span><strong>{controller.index + 1}</strong><small>{allComplete ? "All traces complete" : "Shorter traces stay pinned while longer traces continue"}</small></div></section>

      <section className="hcx-analysis"><div className="hcx-section-heading"><span className="hcx-section-label">FINAL METRICS</span><h2>Compare the work behind each route.</h2><p>Metrics come directly from each backend trace, so route quality and search effort remain visible together.</p></div><div className="hcx-table-wrap"><table><caption className="sr-only">Final heuristic comparison metrics</caption><thead><tr><th scope="col">Heuristic</th><th scope="col">Formula</th><th scope="col">Expanded</th><th scope="col">Discovered</th><th scope="col">Max frontier</th><th scope="col">Path cost</th><th scope="col">Runtime</th><th scope="col">Status</th></tr></thead><tbody>{runs.map((run) => <tr key={run.heuristic}><th scope="row"><span className="hcx-dot" style={{ background: COLORS[run.heuristic] }} />{displayHeuristic(run.heuristic)}</th><td className="mono">{run.heuristic_formula || FORMULA_FALLBACK[run.heuristic].formula}</td><td>{formatMetric(run.expanded)}</td><td>{formatMetric(run.discovered)}</td><td>{formatMetric(run.max_frontier)}</td><td>{formatMetric(run.path_cost)}</td><td>{formatMetric(run.execution_time, " ms")}</td><td><span className={run.reached ? "hcx-table-status reached" : "hcx-table-status"}>{run.reached ? "Reached" : "No route"}</span></td></tr>)}</tbody></table></div></section>
    </> : <section className="hcx-empty"><span className="hcx-section-label">READY TO EXPLORE</span><h2>Run one seeded problem through four real A* traces.</h2><p>The panels, formulas, timeline, and metrics will populate from the backend comparison engine. No prerecorded animation is used.</p></section>}
  </main>;
}

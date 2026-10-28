import { Download, FastForward, Pause, Play, RotateCcw, SkipBack, SkipForward, SlidersHorizontal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { createExecution, exportExecutionUrl } from "../api";
import { AlgorithmStateVisualizer } from "../components/AlgorithmStateVisualizer";
import { ExecutionTimeline } from "../components/ExecutionTimeline";
import { GridVisualizer } from "../components/GridVisualizer";
import { MetricsPanel } from "../components/MetricsPanel";
import { StateLegend } from "../components/StateLegend";
import { ANIMATION_SPEEDS, useAnimationController, type AnimationSpeed } from "../hooks/useAnimationController";
import type { AlgorithmEvent, ExecutionResponse } from "../types";

const defaultConfig = { rows: 14, cols: 22, start: "1,1", goal: "12,20", obstacle_density: 0.18, heuristic: "manhattan", seed: 482193 };

export function VisualizerPage() {
  const { algorithmId = "astar-grid" } = useParams();
  const isGrid = algorithmId === "astar-grid" || algorithmId === "greedy-best-first-grid" || algorithmId === "weighted-astar-grid";
  const [config, setConfig] = useState(defaultConfig);
  const [execution, setExecution] = useState<ExecutionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const events = execution?.events ?? [];
  const controller = useAnimationController(events, { baseDelayMs: 420 });
  const event: AlgorithmEvent | undefined = controller.item;
  const summary = useMemo(() => event?.event_type.replaceAll("_", " ") ?? "READY", [event]);

  useEffect(() => {
    controller.restart();
  }, [execution, controller.restart]);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const runConfig = isGrid
        ? config
        : algorithmId === "minimax-alpha-beta"
          ? { depth: 3, branching_factor: 3, seed: config.seed, alpha_beta: true }
          : algorithmId === "tic-tac-toe"
            ? { board: ["", "", "", "", "X", "", "", "", "O"], player: "X", max_depth: 9, alpha_beta: true }
            : algorithmId === "connect-four"
              ? { max_depth: 3, alpha_beta: true }
              : algorithmId === "astar-15-puzzle"
                ? { board: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 0, 15], max_expansions: 10000 }
                : algorithmId.includes("scheduling")
                  ? { jobs: 4, machines: 3, slots: 12, max_iterations: 100, seed: config.seed }
                  : algorithmId.includes("tsp")
                    ? { num_cities: 8, max_iterations: 40, seed: config.seed }
                    : algorithmId.includes("n-queens")
                      ? { n: 8, max_iterations: 80, seed: config.seed }
                      : { max_iterations: 80, seed: config.seed };
      setExecution(await createExecution(algorithmId, runConfig));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start the execution");
    } finally {
      setLoading(false);
    }
  };

  const setNumber = (key: "rows" | "cols" | "seed", value: string) => setConfig((current) => ({ ...current, [key]: Number(value) }));

  return <section className="workspace page-width page-top">
    <div className="workspace-header">
      <div><span className="eyebrow">VISUALIZATION WORKSPACE · {algorithmId.toUpperCase()}</span><h1>{isGrid ? "Watch the search frontier unfold." : "Inspect the algorithm's decisions."}</h1><p>{isGrid ? "Configure a reproducible grid, then inspect every decision the engine makes." : "The registry selects a real backend engine and exposes its replayable event trace."}</p></div>
      <div className="workspace-status" aria-live="polite"><span className="status-dot" /> {loading ? "EXECUTING" : execution ? execution.status.toUpperCase() : "READY"}<small className="mono">{event ? summary : "No execution loaded"}</small></div>
    </div>
    <div className="workspace-layout">
      <aside className="config-panel">
        <div className="panel-title"><SlidersHorizontal size={16} /> CONFIGURATION</div>
        {isGrid && <>
          <label>Grid rows<input type="number" min={4} max={40} value={config.rows} onChange={(e) => setNumber("rows", e.target.value)} /></label>
          <label>Grid columns<input type="number" min={4} max={60} value={config.cols} onChange={(e) => setNumber("cols", e.target.value)} /></label>
          <div className="two-fields"><label>Start<input value={config.start} onChange={(e) => setConfig({ ...config, start: e.target.value })} /></label><label>Goal<input value={config.goal} onChange={(e) => setConfig({ ...config, goal: e.target.value })} /></label></div>
          <label>Heuristic<select value={config.heuristic} onChange={(e) => setConfig({ ...config, heuristic: e.target.value })}><option value="manhattan">Manhattan</option><option value="euclidean">Euclidean</option><option value="chebyshev">Chebyshev</option><option value="zero">Zero / Dijkstra</option></select></label>
          <label>Obstacle density <span className="range-value">{Math.round(config.obstacle_density * 100)}%</span><input type="range" min="0" max="0.45" step="0.01" value={config.obstacle_density} onChange={(e) => setConfig({ ...config, obstacle_density: Number(e.target.value) })} /></label>
        </>}
        <label>Seed<input type="number" value={config.seed} onChange={(e) => setNumber("seed", e.target.value)} /></label>
        <button type="button" className="button button-dark full-width" onClick={run} disabled={loading}>{loading ? "Running engine…" : `Run ${algorithmId}`}</button>
        {execution && <div className="export-actions"><a className="text-link" href={exportExecutionUrl(execution.execution_id, "json")} target="_blank" rel="noreferrer"><Download size={14} /> JSON</a><a className="text-link" href={exportExecutionUrl(execution.execution_id, "csv")} target="_blank" rel="noreferrer"><Download size={14} /> CSV</a></div>}
        {error && <div className="error-box" role="alert">{error}</div>}
        <StateLegend className="legend" />
      </aside>
      <div className="visual-column">
        <div className="visual-card">
          <div className="visual-card-head"><span><b>{summary}</b><small className="mono">{event ? `iteration ${event.iteration}` : "Run the engine to begin"}</small></span><span className="mono">{event?.current_node ? `current ${event.current_node}` : algorithmId}</span></div>
          {isGrid ? <div className="grid-stage"><GridVisualizer event={event} /></div> : <AlgorithmStateVisualizer algorithmId={algorithmId} event={event} />}
          <div className="playback" aria-label="Visualizer playback controls">
            <button type="button" className="icon-button" onClick={controller.restart} disabled={!events.length} aria-label="Restart execution"><RotateCcw size={16} /></button>
            <button type="button" className="icon-button" onClick={controller.stepBackward} disabled={!events.length || controller.index === 0} aria-label="Previous step"><SkipBack size={16} /></button>
            <button type="button" className="play-button" onClick={controller.isPlaying ? controller.pause : controller.resume} disabled={!events.length || controller.isComplete} aria-label={controller.isPlaying ? "Pause" : "Play"}>{controller.isPlaying ? <Pause size={16} /> : <Play size={16} fill="currentColor" />}</button>
            <button type="button" className="icon-button" onClick={controller.stepForward} disabled={!events.length || controller.isComplete} aria-label="Next step"><SkipForward size={16} /></button>
            <button type="button" className="icon-button" onClick={controller.fastForward} disabled={!events.length || controller.isComplete} aria-label="Fast-forward execution" title="Fast-forward (8×)"><FastForward size={16} /></button>
            <button type="button" className="finish-button" onClick={controller.finish} disabled={!events.length || controller.isComplete}>Finish</button>
            <div className="progress-track" role="progressbar" aria-label={`Execution progress ${Math.round(controller.progress)} percent`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(controller.progress)}><span style={{ width: `${controller.progress}%` }} /></div>
            <span className="mono step-count">{events.length ? `${controller.index + 1} / ${events.length}` : "—"}</span>
            <label className="playback-speed">Speed<select aria-label="Execution speed" value={controller.speed} onChange={(e) => controller.setSpeed(Number(e.target.value) as AnimationSpeed)}>{ANIMATION_SPEEDS.map((speed) => <option key={speed} value={speed}>{speed}×</option>)}</select></label>
          </div>
        </div>
        <div className="metrics-card"><div className="panel-title">EXECUTION METRICS</div><MetricsPanel event={event} /></div>
        <div className="lower-panels"><div className="subpanel"><div className="panel-title">FRONTIER <span className="count-badge">{event?.frontier.length ?? 0}</span></div><div className="queue-list">{(event?.frontier ?? []).slice(0, 7).map((item) => <div key={item.node}><span className="mono">{item.node}</span><span>g {item.g} · h {item.h} · <b>f {item.f}</b></span></div>)}{!event?.frontier.length && <small className="muted">Algorithm-specific state appears in the visualization pane.</small>}</div></div><div className="subpanel timeline-panel"><div className="panel-title">EVENT TIMELINE</div><ExecutionTimeline events={events} activeIndex={controller.index} onSelect={controller.seek} /></div></div>
      </div>
    </div>
  </section>;
}

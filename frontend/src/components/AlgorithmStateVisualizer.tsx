import type { AlgorithmEvent } from "../types";

function Board({ values, n, labels }: { values: unknown[]; n: number; labels?: string[] }) {
  return <div className="state-board" style={{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }}>{values.map((value, index) => <div className="state-tile" key={index}>{labels?.[index] ?? String(value ?? "·")}</div>)}</div>;
}

export function AlgorithmStateVisualizer({ algorithmId, event }: { algorithmId: string; event?: AlgorithmEvent }) {
  const state = event?.state;
  if (algorithmId.includes("15-puzzle") && Array.isArray(state)) return <div className="state-visual"><span className="eyebrow">PUZZLE STATE</span><Board values={state} n={4} labels={state.map((value) => value === 0 ? "" : String(value))} /></div>;
  if (algorithmId.includes("n-queens") && Array.isArray(state)) {
    const n = state.length;
    return <div className="state-visual"><span className="eyebrow">QUEENS STATE · SCORE {String(event?.metrics.current_score ?? "—")}</span><div className="state-board" style={{ gridTemplateColumns: `repeat(${n}, minmax(0, 1fr))` }}>{Array.from({ length: n * n }, (_, index) => { const row = Math.floor(index / n); const col = index % n; return <div className={`state-tile chess ${Number(state[row]) === col ? "queen" : ""}`} key={index}>{Number(state[row]) === col ? "♛" : ""}</div>; })}</div></div>;
  }
  if (algorithmId.includes("tic-tac-toe") && event?.current_node) return <div className="state-visual"><span className="eyebrow">BOARD STATE</span><Board values={event.current_node.split("")} n={3} labels={event.current_node.split("").map((value) => value === "." ? "" : value)} /></div>;
  if (Array.isArray(state)) return <div className="state-visual"><span className="eyebrow">CURRENT STATE</span><div className="state-pill-list">{state.slice(0, 18).map((value, index) => <span key={index} className="mono">{String(value)}</span>)}</div></div>;
  return <div className="generic-state"><pre>{event ? JSON.stringify({ current: event.current_node, candidate: event.candidate, metadata: event.metadata }, null, 2) : "The event state will appear here."}</pre></div>;
}

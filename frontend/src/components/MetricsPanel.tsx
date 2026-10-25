import type { AlgorithmEvent } from "../types";

export function MetricsPanel({ event }: { event?: AlgorithmEvent }) {
  const metrics = event?.metrics ?? {};
  return <div className="metrics-grid">
    <div><span>Expanded</span><strong>{metrics.nodes_expanded ?? 0}</strong></div>
    <div><span>Generated</span><strong>{metrics.nodes_generated ?? 0}</strong></div>
    <div><span>Path cost</span><strong>{metrics.path_cost ?? "—"}</strong></div>
    <div><span>Frontier</span><strong>{event?.frontier.length ?? 0}</strong></div>
  </div>;
}

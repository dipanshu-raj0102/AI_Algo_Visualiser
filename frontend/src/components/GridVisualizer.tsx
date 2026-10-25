import type { AlgorithmEvent } from "../types";

export function GridVisualizer({ event }: { event?: AlgorithmEvent }) {
  const grid = event?.metadata.grid as { rows: number; cols: number; obstacles: string[] } | undefined;
  const rows = grid?.rows ?? 14;
  const cols = grid?.cols ?? 22;
  const obstacles = new Set(grid?.obstacles ?? []);
  const explored = new Set(event?.explored ?? []);
  const frontier = new Set((event?.frontier ?? []).map((item) => item.node));
  const path = new Set(event?.path ?? []);
  const start = (event?.metadata.start as string | undefined) ?? "1,1";
  const goal = (event?.metadata.goal as string | undefined) ?? "12,20";
  const current = event?.current_node;

  return <div className="grid-visualizer" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }} aria-label="A star grid visualization">
    {Array.from({ length: rows * cols }, (_, index) => {
      const node = `${Math.floor(index / cols)},${index % cols}`;
      const state = node === start ? "start" : node === goal ? "goal" : node === current ? "current" : path.has(node) ? "path" : obstacles.has(node) ? "obstacle" : frontier.has(node) ? "frontier" : explored.has(node) ? "explored" : "";
      return <div key={node} className={`grid-cell ${state}`} title={`${node}${state ? ` · ${state}` : ""}`} />;
    })}
  </div>;
}

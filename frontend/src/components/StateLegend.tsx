const STATES = [
  ["start", "Start"],
  ["goal", "Goal"],
  ["obstacle", "Obstacle"],
  ["frontier", "Frontier"],
  ["explored", "Explored"],
  ["current", "Current"],
  ["path", "Final path"],
] as const;

export function StateLegend({ className = "" }: { className?: string }) {
  return <div className={`state-legend ${className}`.trim()} aria-label="Grid state legend">
    {STATES.map(([state, label]) => <span key={state}><i className={`legend-swatch ${state}`} />{label}</span>)}
  </div>;
}

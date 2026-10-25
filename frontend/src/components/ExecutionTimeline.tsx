import type { AlgorithmEvent } from "../types";

export function ExecutionTimeline({ events, activeIndex, onSelect }: { events: AlgorithmEvent[]; activeIndex: number; onSelect: (index: number) => void }) {
  return <div className="timeline">
    {events.map((event, index) => <button key={`${event.iteration}-${index}`} className={index === activeIndex ? "timeline-item active" : "timeline-item"} onClick={() => onSelect(index)}>
      <span className="timeline-dot" />
      <span><b>{event.event_type.replaceAll("_", " ")}</b><small>step {index + 1} · {event.current_node ?? "engine"}</small></span>
    </button>)}
  </div>;
}

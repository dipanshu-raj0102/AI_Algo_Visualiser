export type HeuristicName = "manhattan" | "euclidean" | "chebyshev" | "zero";

export const HEURISTIC_ORDER: readonly HeuristicName[] = ["manhattan", "euclidean", "chebyshev", "zero"];

export type ComparisonFrontierItem = {
  node: string;
  g: number;
  h: number;
  f: number;
};

export type ComparisonEvent = {
  iteration: number;
  event_type: string;
  current_node: string | null;
  frontier: ComparisonFrontierItem[];
  explored: string[];
  path: string[];
  metrics: Record<string, number | string | boolean | null>;
  metadata: Record<string, unknown>;
};

export type ComparisonProblem = {
  rows: number;
  cols: number;
  start: string;
  goal: string;
  obstacles: string[];
  obstacle_density?: number;
  movement_model?: string;
  cost_model?: string;
  seed?: number;
  signature?: string;
};

export type HeuristicSummary = {
  heuristic: HeuristicName;
  heuristic_name: string;
  heuristic_formula: string;
  heuristic_description: string;
  heuristic_assumptions: string;
  heuristic_suitability: string;
  status: string;
  path_cost: number | null;
  path_length: number;
  nodes_expanded: number;
  nodes_generated: number;
  expanded: number;
  discovered: number;
  max_frontier: number;
  explored_cells: number;
  execution_time: number;
  reached: boolean;
  steps: number;
  event_count: number;
};

export type ComparisonRun = HeuristicSummary & {
  problem: ComparisonProblem;
  events: ComparisonEvent[];
};

export type ComparisonExecution = {
  executionId: string;
  status: string;
  runs: ComparisonRun[];
  problem: ComparisonProblem;
};

const HEURISTICS = new Set<HeuristicName>(HEURISTIC_ORDER);

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null ? value as Record<string, unknown> : {};
}

function asNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function asString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asBoolean(value: unknown, fallback = false): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function parseProblem(value: unknown): ComparisonProblem {
  const raw = asRecord(value);
  return {
    rows: asNumber(raw.rows, 14),
    cols: asNumber(raw.cols, 22),
    start: asString(raw.start, "1,1"),
    goal: asString(raw.goal, "12,20"),
    obstacles: Array.isArray(raw.obstacles) ? raw.obstacles.filter((item): item is string => typeof item === "string") : [],
    obstacle_density: typeof raw.obstacle_density === "number" ? raw.obstacle_density : undefined,
    movement_model: typeof raw.movement_model === "string" ? raw.movement_model : undefined,
    cost_model: typeof raw.cost_model === "string" ? raw.cost_model : undefined,
    seed: typeof raw.seed === "number" ? raw.seed : undefined,
    signature: typeof raw.signature === "string" ? raw.signature : undefined,
  };
}

function parseEvent(value: unknown): ComparisonEvent {
  const raw = asRecord(value);
  const metricsRaw = asRecord(raw.metrics);
  const frontier = Array.isArray(raw.frontier) ? raw.frontier.map((item) => {
    const frontierItem = asRecord(item);
    return {
      node: asString(frontierItem.node),
      g: asNumber(frontierItem.g),
      h: asNumber(frontierItem.h),
      f: asNumber(frontierItem.f),
    };
  }).filter((item) => item.node.length > 0) : [];
  return {
    iteration: asNumber(raw.iteration),
    event_type: asString(raw.event_type, "STATE_UPDATED"),
    current_node: typeof raw.current_node === "string" ? raw.current_node : null,
    frontier,
    explored: Array.isArray(raw.explored) ? raw.explored.filter((item): item is string => typeof item === "string") : [],
    path: Array.isArray(raw.path) ? raw.path.filter((item): item is string => typeof item === "string") : [],
    metrics: Object.fromEntries(Object.entries(metricsRaw).filter(([, item]) => typeof item === "number" || typeof item === "string" || typeof item === "boolean" || item === null)) as ComparisonEvent["metrics"],
    metadata: asRecord(raw.metadata),
  };
}

function parseSummary(value: unknown, heuristic: HeuristicName, events: ComparisonEvent[]): HeuristicSummary {
  const raw = asRecord(value);
  const finalMetrics = events.at(-1)?.metrics ?? {};
  const numericMetric = (name: string, fallback = 0) => asNumber(raw[name] ?? finalMetrics[name], fallback);
  const reached = asBoolean(raw.reached ?? finalMetrics.reached, events.at(-1)?.event_type === "COMPLETED");
  return {
    heuristic,
    heuristic_name: asString(raw.heuristic_name, displayHeuristic(heuristic)),
    heuristic_formula: asString(raw.heuristic_formula, heuristic === "zero" ? "0" : heuristic),
    heuristic_description: asString(raw.heuristic_description),
    heuristic_assumptions: asString(raw.heuristic_assumptions, "Four-way movement with unit edge costs."),
    heuristic_suitability: asString(raw.heuristic_suitability),
    status: asString(raw.status, reached ? "completed" : "failed"),
    path_cost: typeof (raw.path_cost ?? finalMetrics.path_cost) === "number" ? Number(raw.path_cost ?? finalMetrics.path_cost) : null,
    path_length: numericMetric("path_length"),
    nodes_expanded: numericMetric("nodes_expanded", numericMetric("expanded")),
    nodes_generated: numericMetric("nodes_generated", numericMetric("discovered")),
    expanded: numericMetric("expanded", numericMetric("nodes_expanded")),
    discovered: numericMetric("discovered", numericMetric("nodes_generated")),
    max_frontier: numericMetric("max_frontier", numericMetric("max_frontier_size")),
    explored_cells: numericMetric("explored_cells"),
    execution_time: numericMetric("execution_time"),
    reached,
    steps: numericMetric("steps", events.length),
    event_count: numericMetric("event_count", events.length),
  };
}

/** Normalize the comparison engine's nested `final_state.metadata.runs` payload. */
export function parseComparisonExecution(payload: unknown): ComparisonExecution | null {
  const root = asRecord(payload);
  const finalState = asRecord(root.final_state);
  const metadata = asRecord(finalState.metadata);
  const rawRuns = Array.isArray(metadata.runs) ? metadata.runs : [];
  const fallbackProblem = parseProblem(metadata.problem);
  const runs = rawRuns.flatMap((value): ComparisonRun[] => {
    const raw = asRecord(value);
    const heuristicValue = raw.heuristic;
    if (!HEURISTICS.has(heuristicValue as HeuristicName)) return [];
    const heuristic = heuristicValue as HeuristicName;
    const rawEvents = Array.isArray(raw.events) ? raw.events : Array.isArray(raw.trace) ? raw.trace : [];
    const events = rawEvents.map(parseEvent);
    if (events.length === 0) return [];
    const problem = parseProblem(raw.problem ?? fallbackProblem);
    return [{ ...parseSummary(raw, heuristic, events), problem, events }];
  });
  if (runs.length === 0) return null;
  const orderedRuns = HEURISTIC_ORDER.flatMap((heuristic) => runs.filter((run) => run.heuristic === heuristic));
  return {
    executionId: asString(root.execution_id),
    status: asString(root.status, "completed"),
    runs: orderedRuns,
    problem: orderedRuns[0]?.problem ?? fallbackProblem,
  };
}

export function eventAt(run: ComparisonRun, index: number): ComparisonEvent | undefined {
  return run.events[Math.min(Math.max(index, 0), Math.max(0, run.events.length - 1))];
}

export function displayHeuristic(heuristic: HeuristicName): string {
  return heuristic === "zero" ? "Zero / Dijkstra" : heuristic.charAt(0).toUpperCase() + heuristic.slice(1);
}

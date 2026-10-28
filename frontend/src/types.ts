export type AlgorithmEvent = {
  iteration: number;
  event_type: string;
  current_node: string | null;
  frontier: Array<{ node: string; g: number; h: number; f: number }>;
  explored: string[];
  path: string[];
  state?: unknown;
  candidate?: unknown;
  explanation?: string | null;
  metrics: Record<string, number | string | boolean | null>;
  metadata: Record<string, unknown>;
};

export type ExecutionResponse = {
  execution_id: string;
  algorithm_id: string;
  status: string;
  events: AlgorithmEvent[];
  final_state: AlgorithmEvent;
};

export type AlgorithmMetadata = {
  id: string;
  name: string;
  category: string;
  description: string;
  difficulty: string;
  visualization_type: string;
  supports_step_execution: boolean;
  supports_comparison: boolean;
};

export type ComparisonResponse = {
  comparison_id: string;
  results: ExecutionResponse[];
  summary: { algorithms: Array<Record<string, unknown>> };
};

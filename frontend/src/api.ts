import type { AlgorithmMetadata, ComparisonResponse, ExecutionResponse } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { headers: { "Content-Type": "application/json" }, ...init });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export const getAlgorithms = () => request<AlgorithmMetadata[]>("/api/v1/algorithms");

export const createExecution = (algorithmId: string, config: Record<string, unknown>) =>
  request<ExecutionResponse>("/api/v1/executions", { method: "POST", body: JSON.stringify({ algorithm_id: algorithmId, config }) });

export const createComparison = (algorithmIds: string[], config: Record<string, unknown>) =>
  request<ComparisonResponse>("/api/v1/comparisons", { method: "POST", body: JSON.stringify({ algorithm_ids: algorithmIds, config }) });

export const exportExecutionUrl = (executionId: string, format: "json" | "csv") => `${API_URL}/api/v1/executions/${executionId}/export?format=${format}`;

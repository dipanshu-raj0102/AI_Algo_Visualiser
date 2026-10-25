import type { AlgorithmMetadata, ExecutionResponse } from "./types";

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

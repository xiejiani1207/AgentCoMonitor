const BASE = "/api";

export interface Task {
  task_id: string;
  title: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Trace {
  trace_id: string;
  task_id: string;
  agent_name: string;
  agent_role: string | null;
  parent_trace_id: string | null;
  start_time: string;
  end_time: string | null;
  duration_ms: number | null;
  input_prompt: string | null;
  output_content: string | null;
  token_used: number | null;
  status: string;
  error_message: string | null;
  quality_score: number | null;
}

export interface AnomalyEvent {
  id: number;
  trace_id: string | null;
  task_id: string;
  anomaly_type: string;
  severity: string;
  layer: string;
  description: string;
  suggestion: string | null;
  created_at: string;
}

export interface QualityScore {
  trace_id: string;
  accuracy: number | null;
  completeness: number | null;
  relevance: number | null;
  compliance: number | null;
  timeliness: number | null;
  overall_score: number;
  eval_method: string | null;
  created_at: string;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  tasks: (limit = 20) => get<Task[]>(`/tasks?limit=${limit}`),
  task: (id: string) => get<Task>(`/tasks/${id}`),
  traces: (taskId: string) => get<Trace[]>(`/traces?task_id=${taskId}&limit=50`),
  trace: (id: string) => get<Trace>(`/traces/${id}`),
  anomalies: (taskId?: string) =>
    get<AnomalyEvent[]>(`/anomalies?limit=50${taskId ? `&task_id=${taskId}` : ""}`),
  quality: (traceId: string) => get<QualityScore>(`/quality/${traceId}`),
};

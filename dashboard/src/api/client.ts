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

export interface SensitiveWord {
  id: number;
  word: string;
  category: string;
  created_at: string;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `${res.status}`);
  }
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "DELETE" });
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
  sensitiveWords: () => get<SensitiveWord[]>("/sensitive-words"),
  addSensitiveWord: (word: string, category: string) =>
    post<SensitiveWord>("/sensitive-words", { word, category }),
  deleteSensitiveWord: (id: number) => del<{ deleted: boolean }>(`/sensitive-words/${id}`),
};

// 后端存的是 naive UTC（datetime.utcnow()），API 返回无时区后缀的 ISO 字符串。
// JS 的 new Date() 会把无时区字符串当本地时间解析，导致显示差 8 小时（UTC+8）。
// 这里补 "Z" 显式按 UTC 解析，再转本地时区显示。
export function formatTime(iso: string): string {
  return new Date(iso.endsWith("Z") ? iso : `${iso}Z`).toLocaleString("zh-CN");
}

// ---- 投顾 demo 服务（8001）----

export interface ViolationItem {
  sentence: string;
  words: string[];
}

export interface AdvisoryReport {
  stock_code: string | null;
  stock_name: string | null;
  technical_report: string;
  fundamental_report: string;
  risk_report: string;
  decision: string;
  compliance_result: string;
  compliance_score: number | null;
  final_output: string;
  violations: ViolationItem[];
}

export interface TraceSummary {
  agent_name: string;
  status: string;
  overall_score: number | null;
}

export interface MonitoringSummary {
  task_id: string;
  traces: TraceSummary[];
  anomaly_count: number;
  suggestion_count: number;
  avg_quality_score: number | null;
  min_compliance: number | null;
}

export interface FeedbackItem {
  target_agent: string;
  dimension: string;
  instruction: string;
  priority: number;
}

export interface RankedResult {
  agent_name: string;
  quality_score: number;
  rank: number;
  recommendation: string;
}

export interface ChatResponse {
  query: string;
  report: AdvisoryReport;
  monitoring: MonitoringSummary;
  demo_mode: boolean;
  feedback: FeedbackItem[];
  ranking: RankedResult[];
}

export async function chat(query: string, demoMode = false, history: string[] = []): Promise<ChatResponse> {
  const res = await fetch("/advisory/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, demo_mode: demoMode, history }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail || `请求失败 (${res.status})`);
  }
  return res.json();
}

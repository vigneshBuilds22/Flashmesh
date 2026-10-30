export type Severity = "low" | "medium" | "high" | "critical";

export interface StateJSON {
  primary_root_cause: string;
  secondary_effects: string[];
  dependency_chain: string[];
  severity: Severity;
  recommended_search_query: string;
}
export interface GraphNode { id: string; label: string; kind: "root_cause" | "dependency" | "effect" }
export interface GraphEdge { source: string; target: string; relation: string }
export interface StateGraph { state: StateJSON; nodes: GraphNode[]; edges: GraphEdge[] }
export interface SearchHit { title: string; url: string; snippet: string; score: number | null }
export interface Grounding { provider: string; query: string; answer: string | null; results: SearchHit[] }
export interface Reasoning {
  root_cause_analysis: string;
  remediation_plan: string[];
  fix_recommendation: string;
  confidence_score: number;
}
export interface Metrics {
  original_tokens: number;
  state_tokens: number;
  tokens_saved: number;
  reduction_pct: number;
  compression_ratio: number;
  baseline_cost_usd: number;
  flashmesh_cost_usd: number;
  cost_saved_usd: number;
  cost_reduction_pct: number;
  pipeline_tokens_used: number;
  dedup_lines_removed: number;
  stage_latency_ms: Record<string, number>;
  note: string;
}
export interface AnalysisResult {
  upload_id: string;
  filename: string;
  mock: boolean;
  log_preview: string;
  state_graph: StateGraph;
  grounding: Grounding;
  reasoning: Reasoning;
  metrics: Metrics;
}
export interface UploadInfo {
  upload_id: string;
  filename: string;
  size_bytes: number;
  line_count: number;
  token_count: number;
  preview: string;
}

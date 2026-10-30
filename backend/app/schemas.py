from typing import Literal
from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high", "critical"]


class StateJSON(BaseModel):
    """The compact machine-readable state FlashMesh reasons over."""
    primary_root_cause: str = ""
    secondary_effects: list[str] = Field(default_factory=list)
    dependency_chain: list[str] = Field(default_factory=list)
    severity: Severity = "medium"
    recommended_search_query: str = ""


class GraphNode(BaseModel):
    id: str
    label: str
    kind: Literal["root_cause", "dependency", "effect"]


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str


class StateGraph(BaseModel):
    state: StateJSON
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class SearchHit(BaseModel):
    title: str
    url: str
    snippet: str
    score: float | None = None


class Grounding(BaseModel):
    provider: str = "tavily"
    query: str
    answer: str | None = None
    results: list[SearchHit] = Field(default_factory=list)


class Reasoning(BaseModel):
    root_cause_analysis: str = ""
    remediation_plan: list[str] = Field(default_factory=list)
    fix_recommendation: str = ""
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)


class UploadInfo(BaseModel):
    upload_id: str
    filename: str
    size_bytes: int
    line_count: int
    token_count: int
    preview: str


class Metrics(BaseModel):
    original_tokens: int
    state_tokens: int
    tokens_saved: int
    reduction_pct: float
    compression_ratio: float
    baseline_cost_usd: float
    flashmesh_cost_usd: float
    cost_saved_usd: float
    cost_reduction_pct: float
    pipeline_tokens_used: int          # real tokens billed across all FlashMesh model calls
    dedup_lines_removed: int
    stage_latency_ms: dict[str, int]
    note: str = ""


class AnalysisResult(BaseModel):
    upload_id: str
    filename: str
    mock: bool = False
    log_preview: str
    state_graph: StateGraph
    grounding: Grounding
    reasoning: Reasoning
    metrics: Metrics

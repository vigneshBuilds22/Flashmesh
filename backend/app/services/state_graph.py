"""State extraction + state graph generation."""
import json
from app.schemas import GraphEdge, GraphNode, StateGraph, StateJSON
from app.services.nebius import NebiusClient
from app.services.tokens import count_tokens, split_by_tokens
from app.config import get_settings

EXTRACT_SYSTEM = """
You are a deterministic infrastructure parser.

Do not explain.
Do not reason.
Do not think step by step.
Do not show chain of thought.
Do not output reasoning.
Do not output reasoning_content.
Do not output markdown.
Do not output code fences.

Output ONLY a valid JSON object.

Schema:

{
  "primary_root_cause": "one precise sentence",
  "secondary_effects": ["short phrases, max 6"],
  "dependency_chain": ["ordered components from root cause to user-visible failure"],
  "severity": "low|medium|high|critical",
  "recommended_search_query": "a web search query with exact error strings, product names and versions"
}

Identify the ROOT cause, not the loudest symptom.

Return ONLY JSON.
"""

MERGE_SYSTEM = """
You are a deterministic infrastructure parser.

Do not explain.
Do not reason.
Do not think step by step.
Do not output reasoning_content.
Do not output markdown.
Do not output code fences.

You receive several partial incident states extracted from consecutive log chunks of ONE incident.
Merge them into a single state using the same JSON schema. Deduplicate; prefer the earliest causal event as root cause.

Return ONLY valid JSON.
"""

def _normalise(d: dict) -> StateJSON:
    sev = str(d.get("severity", "medium")).lower()
    if sev not in {"low", "medium", "high", "critical"}:
        sev = "medium"
    return StateJSON(
        primary_root_cause=str(d.get("primary_root_cause", "")),
        secondary_effects=[str(x) for x in d.get("secondary_effects", [])][:8],
        dependency_chain=[str(x) for x in d.get("dependency_chain", [])][:10],
        severity=sev,
        recommended_search_query=str(d.get("recommended_search_query", "")),
    )


async def extract_state(compacted_logs: str, client: NebiusClient) -> tuple[StateJSON, int]:
    """Returns (state, billed_tokens). Chunks + merges when logs exceed the chunk budget."""
    budget = get_settings().extraction_chunk_tokens
    if count_tokens(compacted_logs) <= budget:
        d, used = await client.chat_json(EXTRACT_SYSTEM, compacted_logs)
        return _normalise(d), used

    total, partials = 0, []
    for chunk in split_by_tokens(compacted_logs, budget):
        d, used = await client.chat_json(EXTRACT_SYSTEM, chunk)
        partials.append(_normalise(d).model_dump())
        total += used
    d, used = await client.chat_json(MERGE_SYSTEM, json.dumps(partials))
    return _normalise(d), total + used


def build_graph(state: StateJSON) -> StateGraph:
    """Turn the flat state into nodes/edges: root -> chain -> effects."""
    nodes: list[GraphNode] = [GraphNode(id="root", label=state.primary_root_cause or "unknown", kind="root_cause")]
    edges: list[GraphEdge] = []
    prev = "root"
    for i, comp in enumerate(state.dependency_chain):
        nid = f"dep{i}"
        nodes.append(GraphNode(id=nid, label=comp, kind="dependency"))
        edges.append(GraphEdge(source=prev, target=nid, relation="propagates_to"))
        prev = nid
    for i, eff in enumerate(state.secondary_effects):
        nid = f"eff{i}"
        nodes.append(GraphNode(id=nid, label=eff, kind="effect"))
        edges.append(GraphEdge(source=prev, target=nid, relation="causes"))
    return StateGraph(state=state, nodes=nodes, edges=edges)


def state_tokens(state: StateJSON) -> int:
    return count_tokens(state.model_dump_json())

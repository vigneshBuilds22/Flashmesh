"""Second model pass: state graph + grounding -> RCA, remediation, fix, confidence."""
import json
from app.schemas import Grounding, Reasoning, StateGraph
from app.services.nebius import NebiusClient

SYSTEM = """
You are a deterministic incident remediation engine.

Do not explain.
Do not think step by step.
Do not output reasoning.
Do not output reasoning_content.
Do not output markdown.

Return ONLY valid JSON.

Schema:

{
  "root_cause_analysis": "",
  "remediation_plan": [],
  "fix_recommendation": "",
  "confidence_score": 0.0
}
"""

async def reason(graph: StateGraph, grounding: Grounding, client: NebiusClient) -> tuple[Reasoning, int]:
    user = json.dumps(
        {
            "state": graph.state.model_dump(),
            "search_answer": grounding.answer,
            "search_results": [h.model_dump(exclude={"score"}) for h in grounding.results],
        }
    )
    d, used = await client.chat_json(SYSTEM, user, max_tokens=6000)
    try:
        conf = max(0.0, min(1.0, float(d.get("confidence_score", 0.5))))
    except (TypeError, ValueError):
        conf = 0.5
    return (
        Reasoning(
            root_cause_analysis=str(d.get("root_cause_analysis", "")),
            remediation_plan=[str(x) for x in d.get("remediation_plan", [])],
            fix_recommendation=str(d.get("fix_recommendation", "")),
            confidence_score=conf,
        ),
        used,
    )

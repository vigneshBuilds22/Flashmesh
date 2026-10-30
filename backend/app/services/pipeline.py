"""End-to-end orchestration: logs -> state -> graph -> grounding -> reasoning -> metrics."""
import time
from app.config import get_settings
from app.schemas import AnalysisResult
from app.services import mock, state_graph, tavily
from app.services.metrics import compute_metrics
from app.services.nebius import NebiusClient
from app.services.preprocess import dedupe_logs
from app.services.reasoning import reason
from app.services.tokens import count_tokens


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


async def run_pipeline(upload_id: str, filename: str, raw: str) -> AnalysisResult:
    s = get_settings()
    lat: dict[str, int] = {}
    used = 0
    client = NebiusClient()

    original_tokens = count_tokens(raw)

    t = time.perf_counter()
    compacted, removed = dedupe_logs(raw)
    lat["preprocess"] = _ms(t)

    # 1. State extraction
    t = time.perf_counter()
    if s.mock_mode:
        state = mock.mock_state()
    else:
        state, u = await state_graph.extract_state(compacted, client)
        used += u
    lat["state_extraction"] = _ms(t)

    # 2. State graph
    t = time.perf_counter()
    graph = state_graph.build_graph(state)
    state_tok = state_graph.state_tokens(state)
    lat["state_graph"] = _ms(t)

    # 3. Grounding
    t = time.perf_counter()
    grounding = mock.mock_grounding(state.recommended_search_query) if s.mock_mode \
        else await tavily.ground(state.recommended_search_query)
    lat["grounding"] = _ms(t)

    # 4. Reasoning
    t = time.perf_counter()
    if s.mock_mode:
        reasoning = mock.mock_reasoning()
    else:
        reasoning, u = await reason(graph, grounding, client)
        used += u
    lat["reasoning"] = _ms(t)

    grounding_tokens = count_tokens(grounding.model_dump_json(exclude={"results": {"__all__": {"score"}}}))
    metrics = compute_metrics(original_tokens, state_tok, grounding_tokens, used, removed, lat, s.mock_mode)

    return AnalysisResult(
        upload_id=upload_id,
        filename=filename,
        mock=s.mock_mode,
        log_preview="\n".join(raw.splitlines()[:60]),
        state_graph=graph,
        grounding=grounding,
        reasoning=reasoning,
        metrics=metrics,
    )

"""Compression + cost metrics.

Baseline  = sending the raw logs to the reasoning model as input.
FlashMesh = reasoning over the compact state (+ grounding) instead.
The cost model is an ESTIMATE driven by BASELINE_*_PRICE_PER_M; `pipeline_tokens_used`
reports real billed tokens so the overhead of extraction is never hidden.
"""
from app.config import get_settings
from app.schemas import Metrics

REASONING_OUTPUT_TOKENS = 600  # typical RCA output, same in both paths


def compute_metrics(
    original_tokens: int,
    state_tok: int,
    grounding_tokens: int,
    pipeline_tokens_used: int,
    dedup_removed: int,
    latency: dict[str, int],
    mock: bool,
) -> Metrics:
    s = get_settings()
    pin, pout = s.baseline_input_price_per_m / 1e6, s.baseline_output_price_per_m / 1e6
    baseline = original_tokens * pin + REASONING_OUTPUT_TOKENS * pout
    # downstream agent reasons over state + grounding rather than raw logs
    flash = (state_tok + grounding_tokens) * pin + REASONING_OUTPUT_TOKENS * pout
    saved_tokens = max(0, original_tokens - state_tok)
    return Metrics(
        original_tokens=original_tokens,
        state_tokens=state_tok,
        tokens_saved=saved_tokens,
        reduction_pct=round(100 * saved_tokens / original_tokens, 1) if original_tokens else 0.0,
        compression_ratio=round(original_tokens / state_tok, 1) if state_tok else 0.0,
        baseline_cost_usd=round(baseline, 5),
        flashmesh_cost_usd=round(flash, 5),
        cost_saved_usd=round(max(0.0, baseline - flash), 5),
        cost_reduction_pct=round(100 * (baseline - flash) / baseline, 1) if baseline else 0.0,
        pipeline_tokens_used=pipeline_tokens_used,
        dedup_lines_removed=dedup_removed,
        stage_latency_ms=latency,
        note=("MOCK MODE: model/search output is canned. " if mock else "")
        + "Cost figures are estimates from configured per-token prices.",
    )

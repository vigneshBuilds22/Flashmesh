# FlashMesh Architecture

```
Raw Logs -> Preprocess (dedupe) -> State Extraction (Nemotron) -> State Graph
         -> Grounding (Tavily)  -> Reasoning (Nemotron)        -> Fix + Metrics
```

| Stage | Module | Model call? | Output |
|---|---|---|---|
| Upload | `routers/logs.py` | no | upload id, token count, preview |
| Preprocess | `services/preprocess.py` | no | normalised + deduplicated logs (`[xN]` counts) |
| State extraction | `services/state_graph.py` | Nemotron | `StateJSON`; chunk + merge if > `EXTRACTION_CHUNK_TOKENS` |
| State graph | `services/state_graph.py` | no | nodes/edges: root -> dependency chain -> effects |
| Grounding | `services/tavily.py` | no (Tavily) | answer + ranked results |
| Reasoning | `services/reasoning.py` | Nemotron | RCA, remediation plan, fix, confidence |
| Metrics | `services/metrics.py` | no | token/cost reduction, per-stage latency |

## Design decisions
- **Two-tier compaction.** A deterministic dedupe pass removes repeated noise before any model call, so extraction is cheaper and fits context.
- **Honest metrics.** `reduction_pct` compares raw-log tokens to state tokens; `pipeline_tokens_used` reports real billed tokens (extraction + reasoning) so overhead is visible. Costs are estimates from configurable prices. FlashMesh pays off when the state is reused across many agent steps instead of re-sending raw logs each time.
- **Provider-agnostic model layer.** Nebius Token Factory is OpenAI-compatible; swap model via `NEBIUS_MODEL`.
- **Fail loudly.** Model/search failures return HTTP 502 with a reason; `MOCK_MODE` is explicit and flagged in every response.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | config status |
| POST | `/api/upload` | multipart `file` -> `UploadInfo` |
| GET | `/api/samples`, POST `/api/samples/{name}` | load bundled sample |
| POST | `/api/analyze/{upload_id}` | run pipeline -> `AnalysisResult` |
| GET | `/api/results/{upload_id}` | fetch stored result |

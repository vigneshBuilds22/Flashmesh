"""FlashMesh validation agent: does the compact state preserve enough to act on?

For each incident log in the manifest:
  raw log -> FlashMesh state (real extraction) -> agent picks ONE of 4 mock tools
and (with --baseline) the same agent also reads the raw log, as a control.

Run from backend/:   python -m scripts.validate_agent [--baseline] [--manifest PATH]
Requires real Nebius credentials (MOCK_MODE must be false: canned output proves nothing).
"""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable

from app.config import get_settings
from app.services.arg_check import ungrounded_args
from app.services.nebius import ModelError, NebiusClient
from app.services.preprocess import dedupe_logs
from app.services.state_graph import extract_state
from app.services.tokens import count_tokens

# ---- The four universal tools (simulated; nothing is executed) -------------------------
# name -> {arg: (type, min, max)}; min/max only apply to ints
TOOL_SPECS: dict[str, dict[str, tuple[type, int | None, int | None]]] = {
    "restart_service": {"service": (str, None, None)},
    "increase_memory_limit": {"service": (str, None, None), "new_limit_mb": (int, 64, 65536)},
    "rollback_release": {"service": (str, None, None), "to_version": (str, None, None)},
    "scale_deployment": {"service": (str, None, None), "replicas": (int, 1, 100)},
}

TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    name: (lambda _n=name, **kw: {"ok": True, "simulated": True, "tool": _n, "args": kw}) for name in TOOL_SPECS
}

AGENT_SYSTEM = """You are a deterministic incident-response agent.
Do not explain. Do not think step by step. Do not output reasoning_content or markdown.

You are an incident-response agent. You receive an incident description and must pick exactly ONE remediation tool.

Tools:
- restart_service(service: str)                         clear a transient fault
- increase_memory_limit(service: str, new_limit_mb: int) memory exhaustion / OOM
- rollback_release(service: str, to_version: str)        a bad deployment or release
- scale_deployment(service: str, replicas: int)          capacity / traffic exhaustion

Use only service names and versions that appear in the evidence. Output ONLY JSON:
{"tool": "<name>", "arguments": {...}, "rationale": "one sentence"}"""


def validate_call(tool: Any, args: Any) -> str | None:
    """Return an error string if the call is malformed, else None."""
    spec = TOOL_SPECS.get(tool) if isinstance(tool, str) else None
    if spec is None:
        return f"unknown tool {tool!r}"
    if not isinstance(args, dict) or set(args) != set(spec):
        return f"arguments must be exactly {sorted(spec)}"
    for key, (typ, lo, hi) in spec.items():
        v = args[key]
        if typ is int:
            if isinstance(v, bool) or not isinstance(v, (int, float)) or int(v) != v:
                return f"{key} must be an integer"
            if not (lo <= int(v) <= hi):
                return f"{key}={v} outside [{lo}, {hi}]"
            args[key] = int(v)
        elif not isinstance(v, str) or not v.strip():
            return f"{key} must be a non-empty string"
    return None


async def decide(client: NebiusClient, context: str, expected: str, raw_log: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        out, used = await client.chat_json(AGENT_SYSTEM, context, max_tokens=4000)
    except ModelError as e:
        return {"error": str(e)[:300], "correct": False, "valid_call": False}
    tool, args = out.get("tool"), out.get("arguments")
    err = validate_call(tool, args)
    bad = ungrounded_args(args, raw_log) if err is None else []
    return {
        "tool": tool,
        "arguments": args,
        "rationale": out.get("rationale", ""),
        "valid_call": err is None,
        "validation_error": err,
        "executed": TOOLS[tool](**args) if err is None else None,
        "correct": err is None and tool == expected,
        "grounded": err is None and not bad,       # service/version strings found in the raw log
        "ungrounded_args": bad,
        "input_tokens_est": count_tokens(context),
        "tokens_billed": used,
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }


def build_report(rows: list[dict[str, Any]], total: int) -> dict[str, Any]:
    def acc(key: str) -> str:
        sel = [r[key] for r in rows if key in r]
        return f"{sum(x['correct'] for x in sel)}/{len(sel)}" if sel else "n/a"

    def grounded(key: str) -> str:
        sel = [r[key] for r in rows if key in r and "grounded" in r[key]]
        return f"{sum(x['grounded'] for x in sel)}/{len(sel)}" if sel else "n/a"

    return {"model": get_settings().nebius_model, "complete": len(rows) == total, "rows": rows,
            "summary": {"flashmesh_correct": acc("flashmesh"), "raw_control_correct": acc("raw_control"),
                        "flashmesh_grounded": grounded("flashmesh"), "raw_control_grounded": grounded("raw_control")}}


async def run(manifest_path: Path, baseline: bool, client: NebiusClient | None = None,
              out: Path | None = None) -> dict[str, Any]:
    client = client or NebiusClient()
    data_dir = Path(get_settings().data_dir) / "sample_logs"
    entries = json.loads(manifest_path.read_text())
    rows: list[dict[str, Any]] = []

    def checkpoint(name: str) -> None:
        print(f"[{len(rows)}/{len(entries)}] {name} done", flush=True)
        if out:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(build_report(rows, len(entries)), indent=2))

    for e in entries:
        raw = (data_dir / e["file"]).read_text(encoding="utf-8", errors="replace")
        compacted, _ = dedupe_logs(raw)
        row: dict[str, Any] = {"file": e["file"], "category": e["category"], "expected_tool": e["expected_tool"],
                               "raw_tokens": count_tokens(raw)}
        try:
            t_ex = time.perf_counter()
            state, extract_tokens = await extract_state(compacted, client)
            row["extraction_latency_ms"] = int((time.perf_counter() - t_ex) * 1000)
        except ModelError as ex:
            row["flashmesh"] = {"error": f"state extraction failed: {str(ex)[:200]}", "correct": False, "valid_call": False}
            rows.append(row)
            checkpoint(e["file"])
            continue
        state_json = state.model_dump_json()
        row["state_tokens"] = count_tokens(state_json)
        row["extraction_tokens_billed"] = extract_tokens
        row["state"] = state.model_dump()
        row["flashmesh"] = await decide(client, f"Incident state:\n{state_json}", e["expected_tool"], raw)
        if baseline:
            row["raw_control"] = await decide(client, f"Raw logs:\n{raw}", e["expected_tool"], raw)
        rows.append(row)
        checkpoint(e["file"])

    return build_report(rows, len(entries))


def print_report(rep: dict[str, Any]) -> None:
    print(f"\nModel: {rep['model']}\n")
    print(f"{'incident':<28}{'raw tok':>9}{'state tok':>10}  {'expected':<24}{'FlashMesh':<30}{'raw control':<30}")
    for r in rep["rows"]:
        def cell(k: str) -> str:
            x = r.get(k)
            if x is None:
                return "-"
            mark = "OK " if x["correct"] else "NO "
            return mark + (x.get("tool") or "error")
        print(f"{r['file']:<28}{r['raw_tokens']:>9}{r.get('state_tokens', 0):>10}  "
              f"{r['expected_tool']:<24}{cell('flashmesh'):<30}{cell('raw_control'):<30}")
    s = rep["summary"]
    print(f"\nCorrect tool      FlashMesh state: {s['flashmesh_correct']}   |   raw-log control: {s['raw_control_correct']}")
    print(f"Args in the logs  FlashMesh state: {s['flashmesh_grounded']}   |   raw-log control: {s['raw_control_grounded']}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", type=Path, default=Path(get_settings().data_dir) / "validation" / "manifest.json")
    ap.add_argument("--baseline", action="store_true", help="also run the agent on the raw logs as a control")
    ap.add_argument("--out", type=Path, default=Path(get_settings().data_dir) / "validation" / "report.json")
    a = ap.parse_args()
    s = get_settings()
    if s.mock_mode or not s.nebius_api_key:
        print("Validation needs real model calls: set MOCK_MODE=false and NEBIUS_API_KEY.", file=sys.stderr)
        return 2
    rep = asyncio.run(run(a.manifest, a.baseline, out=a.out))
    a.out.write_text(json.dumps(rep, indent=2))
    print_report(rep)
    print(f"Full report: {a.out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

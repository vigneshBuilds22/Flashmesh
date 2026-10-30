"""Serves the validation report written by `python -m scripts.validate_agent`."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.config import get_settings
from app.services.arg_check import ungrounded_args

router = APIRouter(prefix="/api", tags=["validation"])


@router.get("/validation")
async def get_validation():
    s = get_settings()
    p = Path(s.data_dir) / "validation" / "report.json"
    if not p.is_file():
        raise HTTPException(404, f"No validation report yet. Looked for: {p.resolve()}")
    rep = json.loads(p.read_text())

    # Older reports predate the argument check: compute it here from the raw logs.
    checked = {"flashmesh": [0, 0], "raw_control": [0, 0]}  # [grounded, checkable]
    for row in rep.get("rows", []):
        try:
            raw = (s.samples_dir / row["file"]).read_text(encoding="utf-8", errors="replace")
        except OSError:
            raw = None
        for key in checked:
            call = row.get(key)
            if not call or not isinstance(call.get("arguments"), dict):
                continue
            if "grounded" not in call and raw is not None:
                bad = ungrounded_args(call["arguments"], raw)
                call["ungrounded_args"], call["grounded"] = bad, not bad
            if "grounded" in call:
                checked[key][1] += 1
                checked[key][0] += bool(call["grounded"])
    summ = rep.setdefault("summary", {})
    for key, (ok, n) in checked.items():
        if n:
            summ[f"{key}_grounded"] = f"{ok}/{n}"
    return rep

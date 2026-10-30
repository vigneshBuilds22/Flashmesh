"""Deterministic log pre-compaction (no model call).

Collapses repeated lines after normalising volatile fields (timestamps, IDs,
numbers) so the model sees each distinct event once with an occurrence count.
"""
import re
from collections import OrderedDict

_TS = re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?Z?\b")
_HEX = re.compile(r"\b[0-9a-f]{8,}\b", re.I)
_NUM = re.compile(r"\b\d+\b")


def _signature(line: str) -> str:
    s = _TS.sub("<ts>", line)
    s = _HEX.sub("<id>", s)
    return _NUM.sub("<n>", s).strip()


def dedupe_logs(text: str) -> tuple[str, int]:
    """Returns (compacted_text, lines_removed)."""
    seen: "OrderedDict[str, list]" = OrderedDict()  # sig -> [first_line, count]
    lines = [l for l in text.splitlines() if l.strip()]
    for line in lines:
        sig = _signature(line)
        if sig in seen:
            seen[sig][1] += 1
        else:
            seen[sig] = [line, 1]
    out = [first if count == 1 else f"{first}  [x{count}]" for first, count in seen.values()]
    return "\n".join(out), len(lines) - len(out)

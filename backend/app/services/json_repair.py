"""Best-effort repair of JSON truncated by max_tokens (additive; used only as a fallback)."""
import json
from typing import Any

_CLOSE = {"{": "}", "[": "]"}


def repair_truncated_json(text: str) -> Any | None:
    """Return the parsed object recovered from truncated JSON, or None.

    Strategy: scan once recording, at every top-level-structure comma, the stack of open
    brackets. Then try (1) closing the text as-is, (2) cutting back to each earlier comma
    and closing there. The first candidate that parses wins, so we keep as much data as
    possible and drop only the dangling fragment.
    """
    stack: list[str] = []
    cuts: list[tuple[int, str]] = []  # (index of comma, closers needed after cutting there)
    in_str = esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in _CLOSE:
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()
        elif ch == "," and stack:
            cuts.append((i, "".join(_CLOSE[b] for b in reversed(stack))))

    candidates: list[str] = []
    # Closing the text as-is is only safe when the cut did not land inside a string or
    # number (a half-written value would be silently accepted as if it were complete).
    if not in_str and not text.rstrip()[-1:].isdigit():
        candidates.append(text + "".join(_CLOSE[b] for b in reversed(stack)))
    candidates += [text[:i] + closers for i, closers in reversed(cuts)]
    for c in candidates:
        try:
            return json.loads(c)
        except json.JSONDecodeError:
            continue
    return None

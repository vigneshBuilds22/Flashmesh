"""Argument grounding: a tool call is only trustworthy if the service/version strings it
uses actually appear in the evidence (the raw log). Catches 'right tool, invented argument'."""


def ungrounded_args(args: dict, raw_log: str) -> list[str]:
    low = raw_log.lower()
    return [k for k, v in args.items() if isinstance(v, str) and v.strip().lower() not in low]

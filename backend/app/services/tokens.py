"""Token counting. Uses tiktoken (cl100k) as a model-agnostic estimator;
falls back to ~4 chars/token if the encoding cannot be loaded offline."""
from functools import lru_cache


@lru_cache
def _enc():
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


def count_tokens(text: str) -> int:
    enc = _enc()
    if enc is None:
        return max(1, len(text) // 4)
    return len(enc.encode(text, disallowed_special=()))


def split_by_tokens(text: str, max_tokens: int) -> list[str]:
    """Split on line boundaries into chunks of <= max_tokens (approx)."""
    chunks, cur, cur_t = [], [], 0
    for line in text.splitlines():
        t = count_tokens(line) + 1
        if cur and cur_t + t > max_tokens:
            chunks.append("\n".join(cur))
            cur, cur_t = [], 0
        cur.append(line)
        cur_t += t
    if cur:
        chunks.append("\n".join(cur))
    return chunks

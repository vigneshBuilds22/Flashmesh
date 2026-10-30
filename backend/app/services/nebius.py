"""Nebius Token Factory client (OpenAI-compatible chat completions)."""
import json
import logging
import re
import httpx
from app.config import get_settings
from app.services.json_repair import repair_truncated_json

log = logging.getLogger("flashmesh.nebius")


class ModelError(RuntimeError):
    pass


def parse_json_loose(text: str) -> dict:
    """Extract a JSON object from model output (handles <think>, ``` fences, prose)."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1:
            raise ModelError(f"Model did not return JSON: {text[:200]!r}")
        if end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        # Fallback: output was cut off (e.g. max_tokens). Recover what we can.
        repaired = repair_truncated_json(text[start:])
        if isinstance(repaired, dict) and repaired:  # never accept an empty object as a result
            log.warning("Recovered truncated JSON from model output (%d chars)", len(text))
            return repaired
        raise ModelError(f"Invalid or truncated JSON from model: {text[:200]!r}")


class NebiusClient:
    def __init__(self) -> None:
        self.s = get_settings()

    async def chat_json(self, system: str, user: str, max_tokens: int = 5000) -> tuple[dict, int]:
        """Returns (parsed_json, total_tokens_billed)."""
        if not self.s.nebius_api_key:
            raise ModelError("NEBIUS_API_KEY is not set (or enable MOCK_MODE=true).")
        payload = {
            "model": self.s.nebius_model,
            "temperature": 0.1,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {self.s.nebius_api_key}"}
        url = f"{self.s.nebius_base_url.rstrip('/')}/chat/completions"
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=payload, headers=headers)
            if r.status_code == 400 and "response_format" in r.text:
                payload.pop("response_format")  # model/endpoint without JSON mode
                r = await client.post(url, json=payload, headers=headers)
        if r.status_code >= 400:
            raise ModelError(f"Nebius error {r.status_code}: {r.text[:300]}")
        data = r.json()
        print("=" * 100)
        print(json.dumps(data, indent=2))
        print("=" * 100)
        choice = data["choices"][0]
        if choice.get("finish_reason") == "length":
            log.warning("Model hit max_tokens (%d); output may be truncated. Reasoning tokens count toward the limit.", max_tokens)
        content = choice["message"]["content"] or ""
        tokens = int((data.get("usage") or {}).get("total_tokens", 0))
        return parse_json_loose(content), tokens

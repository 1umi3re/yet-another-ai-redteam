from __future__ import annotations
import time
import httpx
from airedteam.core.types import Prompt, Response


class AnthropicCompatTarget:
    def __init__(self, *, name: str, base_url: str, model: str, api_key: str, anthropic_version: str = "2023-06-01", max_tokens: int = 1024, system_prompt: str | None = None, timeout: float = 60.0) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        headers = {
            "x-api-key": api_key,
            "anthropic-version": anthropic_version,
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers)

    async def generate(self, prompt: Prompt) -> Response:
        body: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt.text}],
        }
        if self.system_prompt:
            body["system"] = self.system_prompt
        t0 = time.perf_counter()
        r = await self._client.post(f"{self.base_url}/messages", json=body)
        r.raise_for_status()
        latency = int((time.perf_counter() - t0) * 1000)
        data = r.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        usage = data.get("usage") or {}
        return Response(text=text, raw=data, latency_ms=latency, tokens_in=usage.get("input_tokens"), tokens_out=usage.get("output_tokens"))

    async def aclose(self) -> None:
        await self._client.aclose()

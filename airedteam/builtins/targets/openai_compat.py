from __future__ import annotations
import time
import httpx
from airedteam.core.types import Prompt, Response, Message
from airedteam.core.plugins import BaseTarget


class OpenAICompatTarget(BaseTarget):
    def __init__(self, *, name: str, base_url: str, model: str, api_key: str, timeout: float = 60.0, system_prompt: str | None = None, temperature: float | None = None, extra_headers: dict[str, str] | None = None) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.temperature = temperature
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        self._client = httpx.AsyncClient(timeout=timeout, headers=headers)

    async def _post_chat_completions(self, payload: dict) -> Response:
        t0 = time.perf_counter()
        r = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
        r.raise_for_status()
        latency = int((time.perf_counter() - t0) * 1000)
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage") or {}
        return Response(text=text, raw=data, latency_ms=latency, tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"))

    async def generate(self, prompt: Prompt) -> Response:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.append({"role": "user", "content": prompt.text})
        body: dict = {"model": self.model, "messages": msgs}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        return await self._post_chat_completions(body)

    async def chat(self, messages: list[Message]) -> Response:
        msgs = [{"role": m.role, "content": m.text} for m in messages]
        body: dict = {"model": self.model, "messages": msgs}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        return await self._post_chat_completions(body)

    async def aclose(self) -> None:
        await self._client.aclose()


class OpenAICompatNewSessionTarget(OpenAICompatTarget):
    async def _post_chat_completions(self, payload: dict) -> Response:
        payload = dict(payload)
        payload["new_session"] = True
        return await super()._post_chat_completions(payload)

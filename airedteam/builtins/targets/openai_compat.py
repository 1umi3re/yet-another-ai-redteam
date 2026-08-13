from __future__ import annotations

import logging
import time
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, replace

import httpx

from airedteam.builtins.targets.artifact_content import openai_content
from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Message, Prompt, Response

logger = logging.getLogger(__name__)
SESSION_RELEASE_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True)
class _SessionScope:
    session_ids: tuple[str, ...] = ()
    active_session_id: str | None = None
    bound: bool = False
    next_request_starts_session: bool = False


class OpenAICompatTarget(BaseTarget):
    def __init__(
        self,
        *,
        name: str,
        base_url: str,
        model: str,
        api_key: str,
        timeout: float = 300.0,
        system_prompt: str | None = None,
        temperature: float | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.temperature = temperature
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if extra_headers:
            headers.update(extra_headers)
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=30.0), headers=headers)

    def _prepare_chat_completions_payload(
        self,
        payload: dict,
        *,
        request_kind: str,
        messages: list[Message] | None = None,
    ) -> dict:
        return payload

    async def _post_chat_completions(self, payload: dict) -> Response:
        t0 = time.perf_counter()
        r = await self._client.post(f"{self.base_url}/chat/completions", json=payload)
        r.raise_for_status()
        latency = int((time.perf_counter() - t0) * 1000)
        data = r.json()
        message = data["choices"][0].get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            text = "".join(
                str(item.get("text") or "") for item in content if isinstance(item, dict) and item.get("type") == "text"
            )
        else:
            text = str(content or "")
        usage = data.get("usage") or {}
        return Response(
            text=text,
            raw=data,
            latency_ms=latency,
            tokens_in=usage.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens"),
        )

    async def generate(self, prompt: Prompt) -> Response:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.append({"role": "user", "content": openai_content(prompt.text, prompt.artifacts)})
        body: dict = {"model": self.model, "messages": msgs}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        body = self._prepare_chat_completions_payload(body, request_kind="generate")
        return await self._post_chat_completions(body)

    async def check_stream_support(self, prompt: Prompt) -> tuple[bool, str | None]:
        msgs = []
        if self.system_prompt:
            msgs.append({"role": "system", "content": self.system_prompt})
        msgs.append({"role": "user", "content": openai_content(prompt.text, prompt.artifacts)})
        body: dict = {"model": self.model, "messages": msgs, "stream": True}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        body = self._prepare_chat_completions_payload(body, request_kind="stream_check")
        try:
            async with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=body,
            ) as r:
                r.raise_for_status()
                saw_data = False
                async for line in r.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue
                    payload = line.removeprefix("data:").strip()
                    if payload:
                        saw_data = True
                    if payload == "[DONE]":
                        return True, None
                    if saw_data:
                        return True, None
                if saw_data:
                    return True, None
                return False, "stream response did not contain SSE data"
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"

    async def chat(self, messages: list[Message]) -> Response:
        msgs = [{"role": m.role, "content": openai_content(m.text, m.artifacts)} for m in messages]
        body: dict = {"model": self.model, "messages": msgs}
        if self.temperature is not None:
            body["temperature"] = self.temperature
        body = self._prepare_chat_completions_payload(body, request_kind="chat", messages=messages)
        return await self._post_chat_completions(body)

    async def aclose(self) -> None:
        await self._client.aclose()


class OpenAICompatNewSessionTarget(OpenAICompatTarget):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._session_scope: ContextVar[_SessionScope | None] = ContextVar(
            f"openai_compat_session_scope_{id(self)}", default=None
        )
        self._outstanding_sessions: set[str] = set()
        self._persistent_sessions: set[str] = set()
        self._closed = False

    def begin_attempt(self) -> Token:
        """Create an attempt-local scope on a Target shared by concurrent tasks."""
        return self._session_scope.set(_SessionScope())

    async def end_attempt(self, token: Token) -> None:
        """Release every remote device session opened by the current attempt."""
        scope = self._session_scope.get()
        try:
            if scope is not None:
                await self._release_many(scope.session_ids)
        finally:
            self._session_scope.reset(token)

    def bind_session(self, session_id: str, *, new_session: bool) -> None:
        """Bind a cross-request caller (the manual console) to a stable session."""
        value = str(session_id or "").strip()
        if not value:
            raise ValueError("session_id is required")
        self._outstanding_sessions.add(value)
        self._persistent_sessions.add(value)
        self._session_scope.set(
            _SessionScope(
                session_ids=(value,),
                active_session_id=value,
                bound=True,
                next_request_starts_session=bool(new_session),
            )
        )

    def _scope(self) -> _SessionScope:
        scope = self._session_scope.get()
        if scope is None:
            scope = _SessionScope()
            self._session_scope.set(scope)
        return scope

    def _allocate_session(self) -> tuple[_SessionScope, str]:
        scope = self._scope()
        session_id = str(uuid.uuid4())
        self._outstanding_sessions.add(session_id)
        scope = replace(
            scope,
            session_ids=(*scope.session_ids, session_id),
            active_session_id=session_id,
            next_request_starts_session=False,
        )
        self._session_scope.set(scope)
        return scope, session_id

    def _prepare_chat_completions_payload(
        self,
        payload: dict,
        *,
        request_kind: str,
        messages: list[Message] | None = None,
    ) -> dict:
        scope = self._scope()
        transcript_has_assistant = request_kind == "chat" and any(
            message.role == "assistant" for message in messages or []
        )
        starts_independent_conversation = request_kind != "chat" or not transcript_has_assistant

        if scope.bound and scope.active_session_id:
            session_id = scope.active_session_id
            starts_session = scope.next_request_starts_session
            if starts_session:
                scope = replace(scope, next_request_starts_session=False)
                self._session_scope.set(scope)
        elif starts_independent_conversation:
            scope, session_id = self._allocate_session()
            starts_session = True
        elif scope.active_session_id:
            session_id = scope.active_session_id
            starts_session = False
        else:
            # A caller may enter with a pre-existing transcript but without an
            # AutoAgent device binding. Establish one before sending the turn.
            scope, session_id = self._allocate_session()
            starts_session = True

        payload = dict(payload)
        payload["session_id"] = session_id
        if starts_session:
            payload["new_session"] = True
        return payload

    async def release_session(self, session_id: str) -> bool:
        """Idempotently release an AutoAgent device reservation."""
        value = str(session_id or "").strip()
        if not value:
            return False
        body = {
            "model": self.model,
            "messages": [{"role": "user", "content": "-"}],
            "session_id": value,
            "end_session": True,
        }
        response = await self._client.post(
            f"{self.base_url}/chat/completions",
            json=body,
            timeout=httpx.Timeout(SESSION_RELEASE_TIMEOUT_SECONDS, connect=5.0),
        )
        response.raise_for_status()
        self._outstanding_sessions.discard(value)
        self._persistent_sessions.discard(value)
        return True

    async def _release_many(self, session_ids) -> None:
        for session_id in dict.fromkeys(session_ids):
            if session_id not in self._outstanding_sessions:
                continue
            try:
                await self.release_session(session_id)
            except Exception as exc:
                logger.warning("failed to release AutoAgent session %s: %s", session_id, exc)

    async def aclose(self) -> None:
        if self._closed:
            return
        try:
            await self._release_many(
                tuple(self._outstanding_sessions - self._persistent_sessions)
            )
        finally:
            self._closed = True
            await super().aclose()

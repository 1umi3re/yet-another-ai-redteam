from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field, replace
from typing import Any

from airedteam.core.types import AttemptResult, Message, Prompt
from airedteam.engine.input_limits import target_max_input_chars
from airedteam.services.service_context_templates import wrap_transformed_prompt


@dataclass
class _Capture:
    calls: list[dict[str, Any]] = field(default_factory=list)
    selected_prompts: dict[int, Prompt] = field(default_factory=dict)
    final_chat_first_user: Message | None = None
    first_sent_prompt: Prompt | None = None


class ServiceContextTarget:
    """Target proxy that wraps actual outgoing messages and captures auditable evidence."""

    def __init__(self, target, template: dict[str, Any]) -> None:
        self._target = target
        self._template = dict(template)
        self.name = getattr(target, "name", "?")
        self._capture: ContextVar[_Capture | None] = ContextVar(
            f"service_context_capture_{id(self)}", default=None
        )
        for attr in (
            "_airedteam_max_input_chars",
            "_airedteam_input_limit_unit",
            "_airedteam_max_concurrency",
        ):
            if hasattr(target, attr):
                setattr(self, attr, getattr(target, attr))

    def __getattr__(self, name: str):
        return getattr(self._target, name)

    def begin_attempt(self) -> Token:
        return self._capture.set(_Capture())

    def finish_attempt(self, token: Token, attempt: AttemptResult) -> None:
        capture = self._capture.get()
        try:
            if capture is None:
                return
            selected: Prompt | None = None
            if attempt.response is not None:
                selected = capture.selected_prompts.get(id(attempt.response))
            if selected is None and capture.final_chat_first_user is not None:
                first = capture.final_chat_first_user
                selected = Prompt(text=first.text, metadata=first.metadata, artifacts=first.artifacts)
            if selected is None and len(capture.selected_prompts) == 1:
                selected = next(iter(capture.selected_prompts.values()))
            if selected is None:
                selected = capture.first_sent_prompt

            if selected is not None:
                attempt.prompt = selected
            if capture.final_chat_first_user is not None and attempt.conversation:
                replaced = False
                conversation: list[Message] = []
                for message in attempt.conversation:
                    if not replaced and message.role == "user":
                        conversation.append(capture.final_chat_first_user)
                        replaced = True
                    else:
                        conversation.append(message)
                attempt.conversation = conversation

            first_call = capture.calls[0] if capture.calls else None
            selected_call = None
            if attempt.response is not None:
                selected_call = next(
                    (call for call in capture.calls if call.get("response_identity") == id(attempt.response)),
                    None,
                )
            chosen_call = selected_call or first_call
            public_calls = [
                {key: value for key, value in call.items() if key != "response_identity"}
                for call in capture.calls
            ]
            attempt.service_context = {
                "status": (chosen_call or {}).get("status", "no_calls"),
                "template_id": self._template.get("id"),
                "template_version": self._template.get("version"),
                "target_model": self._template.get("target_model"),
                "generator_model": self._template.get("generator_model"),
                "topic": self._template.get("topic"),
                "language": self._template.get("language"),
                "transformed_prompt": (chosen_call or {}).get("transformed_prompt"),
                "sent_prompt": (chosen_call or {}).get("sent_prompt"),
                "fallback_reason": (chosen_call or {}).get("fallback_reason"),
                "calls": public_calls,
            }
        finally:
            self._capture.reset(token)

    def _adapt_text(self, text: str) -> tuple[str, str, str | None]:
        wrapped = wrap_transformed_prompt(str(self._template["template"]), text)
        max_chars = target_max_input_chars(self._target)
        if max_chars is not None and len(wrapped) > max_chars:
            return text, "fallback_input_limit", (
                f"wrapped prompt has {len(wrapped)} characters, exceeding target max_input_chars={max_chars}"
            )
        return wrapped, "applied", None

    async def generate(self, prompt: Prompt):
        sent_text, status, reason = self._adapt_text(prompt.text)
        sent = replace(prompt, text=sent_text)
        capture = self._capture.get()
        call = {
            "kind": "generate",
            "status": status,
            "transformed_prompt": prompt.text,
            "sent_prompt": sent_text,
            "fallback_reason": reason,
            "response_identity": None,
        }
        if capture is not None:
            capture.calls.append(call)
            capture.first_sent_prompt = capture.first_sent_prompt or sent
        response = await self._target.generate(sent)
        if capture is not None:
            call["response_identity"] = id(response)
            capture.selected_prompts[id(response)] = sent
        return response

    async def chat(self, messages: list[Message]):
        sent_messages = list(messages)
        first_user_index = next((idx for idx, msg in enumerate(messages) if msg.role == "user"), None)
        status = "no_user_message"
        reason = None
        transformed_text = sent_text = None
        sent_first: Message | None = None
        if first_user_index is not None:
            original = messages[first_user_index]
            transformed_text = original.text
            sent_text, status, reason = self._adapt_text(original.text)
            sent_first = replace(original, text=sent_text)
            sent_messages[first_user_index] = sent_first
        capture = self._capture.get()
        call = {
            "kind": "chat",
            "status": status,
            "transformed_prompt": transformed_text,
            "sent_prompt": sent_text,
            "fallback_reason": reason,
            "response_identity": None,
        }
        if capture is not None:
            capture.calls.append(call)
            if sent_first is not None:
                capture.final_chat_first_user = sent_first
                sent_prompt = Prompt(
                    text=sent_first.text,
                    metadata=sent_first.metadata,
                    artifacts=sent_first.artifacts,
                )
                capture.first_sent_prompt = capture.first_sent_prompt or sent_prompt
        response = await self._target.chat(sent_messages)
        if capture is not None:
            call["response_identity"] = id(response)
            if sent_first is not None:
                capture.selected_prompts[id(response)] = sent_prompt
        return response

    async def aclose(self) -> None:
        await self._target.aclose()

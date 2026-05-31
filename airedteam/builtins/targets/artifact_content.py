from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from airedteam.core.types import PromptArtifact


def _read_base64(artifact: PromptArtifact) -> str:
    return base64.b64encode(Path(artifact.path).read_bytes()).decode("ascii")


def _data_uri(artifact: PromptArtifact) -> str:
    return f"data:{artifact.media_type};base64,{_read_base64(artifact)}"


def _filename(artifact: PromptArtifact) -> str:
    return artifact.name or Path(artifact.path).name


def openai_content(text: str, artifacts: list[PromptArtifact]) -> str | list[dict[str, Any]]:
    if not artifacts:
        return text
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for artifact in artifacts:
        if artifact.kind == "image":
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _data_uri(artifact)},
                }
            )
        elif artifact.kind == "audio":
            audio_format = Path(artifact.path).suffix.lstrip(".") or "wav"
            content.append(
                {
                    "type": "input_audio",
                    "input_audio": {
                        "data": _read_base64(artifact),
                        "format": audio_format,
                    },
                }
            )
        else:
            content.append(
                {
                    "type": "file",
                    "file": {
                        "filename": _filename(artifact),
                        "file_data": _data_uri(artifact),
                    },
                }
            )
    return content


def anthropic_content(text: str, artifacts: list[PromptArtifact]) -> str | list[dict[str, Any]]:
    if not artifacts:
        return text
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for artifact in artifacts:
        if artifact.kind == "image":
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": artifact.media_type,
                        "data": _read_base64(artifact),
                    },
                }
            )
        elif artifact.kind == "binary" and artifact.media_type == "application/pdf":
            content.append(
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": artifact.media_type,
                        "data": _read_base64(artifact),
                    },
                }
            )
        else:
            content.append(
                {
                    "type": "text",
                    "text": (
                        f"[artifact: {_filename(artifact)}; "
                        f"kind={artifact.kind}; media_type={artifact.media_type}; "
                        f"path={artifact.path}]"
                    ),
                }
            )
    return content

from __future__ import annotations

import html
import json
import math
import mimetypes
import struct
import tempfile
import uuid
import wave
import zipfile
from pathlib import Path

from airedteam.core.types import Prompt, PromptArtifact


_ARTIFACT_KINDS = {
    "image_path": "image",
    "audio_path": "audio",
    "video_path": "video",
    "binary_path": "binary",
}


def artifact_dir(output_dir: str | Path | None = None) -> Path:
    root = Path(output_dir) if output_dir is not None else Path(tempfile.gettempdir()) / "airedteam-converters"
    root.mkdir(parents=True, exist_ok=True)
    return root


def artifact_path(output_dir: str | Path | None, suffix: str) -> Path:
    return artifact_dir(output_dir) / f"{uuid.uuid4().hex}{suffix}"


def artifact_media_type(path: Path) -> str:
    if path.suffix.lower() == ".wav":
        return "audio/wav"
    media_type, _ = mimetypes.guess_type(path.name)
    return media_type or "application/octet-stream"


def artifact_prompt(
    path: Path,
    *,
    source: Prompt,
    output_type: str,
    converter: str,
    extra: dict | None = None,
) -> Prompt:
    metadata = dict(source.metadata)
    metadata.update({
        "output_type": output_type,
        "converter": converter,
        "artifact_path": str(path),
        "source_text": source.text,
    })
    if extra:
        metadata.update(extra)
    artifact = PromptArtifact(
        path=str(path),
        kind=_ARTIFACT_KINDS.get(output_type, "binary"),
        media_type=artifact_media_type(path),
        name=path.name,
        metadata={"output_type": output_type, "converter": converter},
    )
    return Prompt(text=str(path), metadata=metadata, artifacts=[artifact])


def write_svg_text(
    text: str,
    *,
    output_dir: str | Path | None,
    converter: str,
    width: int = 640,
    height: int = 360,
    extra_svg: str = "",
) -> Path:
    path = artifact_path(output_dir, ".svg")
    escaped = html.escape(text)
    content = (
        f"<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{width}\" height=\"{height}\" "
        f"viewBox=\"0 0 {width} {height}\">"
        "<rect width=\"100%\" height=\"100%\" fill=\"white\"/>"
        f"{extra_svg}"
        f"<text x=\"24\" y=\"48\" font-family=\"monospace\" font-size=\"24\" "
        f"fill=\"black\">{escaped}</text>"
        f"<desc>{html.escape(converter)}</desc>"
        "</svg>"
    )
    path.write_text(content)
    return path


def write_pdf_text(text: str, *, output_dir: str | Path | None) -> Path:
    path = artifact_path(output_dir, ".pdf")
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 18 Tf 72 720 Td ({escaped}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream.encode())} >> stream\n{stream}\nendstream endobj\n",
    ]
    body = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(body.encode()))
        body += obj
    xref_offset = len(body.encode())
    body += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for offset in offsets[1:]:
        body += f"{offset:010d} 00000 n \n"
    body += f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
    path.write_bytes(body.encode("latin-1", errors="replace"))
    return path


def write_docx_text(text: str, *, output_dir: str | Path | None) -> Path:
    path = artifact_path(output_dir, ".docx")
    escaped = html.escape(text)
    document = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">"
        f"<w:body><w:p><w:r><w:t>{escaped}</w:t></w:r></w:p></w:body></w:document>"
    )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", "<?xml version=\"1.0\"?><Types/>")
        archive.writestr("word/document.xml", document)
    return path


def write_wav_tone(
    text: str,
    *,
    output_dir: str | Path | None,
    frequency_hz: int = 440,
    volume: float = 0.25,
    duration_s: float | None = None,
) -> Path:
    path = artifact_path(output_dir, ".wav")
    sample_rate = 8000
    duration = duration_s if duration_s is not None else min(2.0, max(0.25, len(text) * 0.03))
    frames = int(sample_rate * duration)
    amplitude = int(max(0.0, min(1.0, volume)) * 32767)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(frames):
            sample = int(amplitude * math.sin(2 * math.pi * frequency_hz * (i / sample_rate)))
            wav.writeframes(struct.pack("<h", sample))
    return path


def write_video_manifest(text: str, *, output_dir: str | Path | None, converter: str) -> Path:
    path = artifact_path(output_dir, ".json")
    payload = {"output_type": "video_path", "converter": converter, "prompt": text}
    path.write_text(json.dumps(payload))
    return path

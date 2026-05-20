from __future__ import annotations

from pathlib import Path

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text


class QRCodeConverter:
    name = "qr_code"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = output_dir

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = (
            "<rect x=\"420\" y=\"36\" width=\"160\" height=\"160\" fill=\"none\" stroke=\"black\"/>"
            "<rect x=\"440\" y=\"56\" width=\"36\" height=\"36\" fill=\"black\"/>"
            "<rect x=\"524\" y=\"56\" width=\"36\" height=\"36\" fill=\"black\"/>"
            "<rect x=\"440\" y=\"140\" width=\"36\" height=\"36\" fill=\"black\"/>"
        )
        path = write_svg_text(prompt.text, output_dir=self.output_dir, converter=self.name, extra_svg=extra)
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

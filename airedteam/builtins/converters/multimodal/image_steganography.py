from __future__ import annotations

import html
from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text
from airedteam.core.types import Prompt


class ImageSteganographyConverter:
    """Embed the prompt as hidden metadata inside an image artifact."""

    name = "image_steganography"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = output_dir

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = f"<metadata>hidden_instruction={html.escape(prompt.text)}</metadata>"
        path = write_svg_text(
            "benign visual carrier",
            output_dir=self.output_dir,
            converter=self.name,
            extra_svg=extra,
        )
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

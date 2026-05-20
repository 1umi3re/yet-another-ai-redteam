from __future__ import annotations

from pathlib import Path

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text


class ImageCompressionConverter:
    name = "image_compression"

    def __init__(self, *, output_dir: str | Path | None = None, quality: int = 75) -> None:
        self.output_dir = output_dir
        self.quality = int(quality)

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = f"<metadata>quality={self.quality}</metadata>"
        path = write_svg_text(prompt.text, output_dir=self.output_dir, converter=self.name, extra_svg=extra)
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

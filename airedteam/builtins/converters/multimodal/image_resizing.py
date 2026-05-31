from __future__ import annotations

from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text
from airedteam.core.types import Prompt


class ImageResizingConverter:
    name = "image_resizing"

    def __init__(self, *, output_dir: str | Path | None = None, width: int = 640, height: int = 360) -> None:
        self.output_dir = output_dir
        self.width = int(width)
        self.height = int(height)

    async def convert(self, prompt: Prompt) -> Prompt:
        path = write_svg_text(
            prompt.text,
            output_dir=self.output_dir,
            converter=self.name,
            width=self.width,
            height=self.height,
        )
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

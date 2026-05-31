from __future__ import annotations

from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text
from airedteam.core.types import Prompt


class ImageRotationConverter:
    name = "image_rotation"

    def __init__(self, *, output_dir: str | Path | None = None, degrees: int = 90) -> None:
        self.output_dir = output_dir
        self.degrees = int(degrees)

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = f'<g transform="rotate({self.degrees} 320 180)"></g>'
        path = write_svg_text(prompt.text, output_dir=self.output_dir, converter=self.name, extra_svg=extra)
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

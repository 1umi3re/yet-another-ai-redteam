from __future__ import annotations

from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text
from airedteam.core.types import Prompt


class ImageColorSaturationConverter:
    name = "image_color_saturation"

    def __init__(self, *, output_dir: str | Path | None = None, saturation: float = 1.0) -> None:
        self.output_dir = output_dir
        self.saturation = float(saturation)

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = f"<metadata>saturation={self.saturation}</metadata>"
        path = write_svg_text(prompt.text, output_dir=self.output_dir, converter=self.name, extra_svg=extra)
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

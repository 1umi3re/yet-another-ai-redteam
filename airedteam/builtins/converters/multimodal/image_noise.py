from __future__ import annotations

from pathlib import Path

from airedteam.core.types import Prompt

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text


class ImageNoiseConverter:
    name = "image_noise"

    def __init__(self, *, output_dir: str | Path | None = None, intensity: float = 0.35) -> None:
        self.output_dir = output_dir
        self.intensity = max(0.0, min(1.0, float(intensity)))

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = (
            f"<metadata>intensity={self.intensity}</metadata>"
            "<filter id=\"noise\">"
            f"<feTurbulence type=\"fractalNoise\" baseFrequency=\"{self.intensity}\" "
            "numOctaves=\"2\" stitchTiles=\"stitch\"/>"
            "<feBlend mode=\"multiply\" in=\"SourceGraphic\"/>"
            "</filter>"
            "<rect width=\"100%\" height=\"100%\" filter=\"url(#noise)\" opacity=\"0.35\"/>"
        )
        path = write_svg_text(
            prompt.text,
            output_dir=self.output_dir,
            converter=self.name,
            extra_svg=extra,
        )
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

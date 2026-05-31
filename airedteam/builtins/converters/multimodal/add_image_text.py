from __future__ import annotations

from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_svg_text
from airedteam.core.types import Prompt


class AddImageTextConverter:
    name = "add_image_text"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = output_dir

    async def convert(self, prompt: Prompt) -> Prompt:
        extra = '<circle cx="560" cy="80" r="44" fill="#e5e7eb" stroke="#111827"/>'
        path = write_svg_text(prompt.text, output_dir=self.output_dir, converter=self.name, extra_svg=extra)
        return artifact_prompt(path, source=prompt, output_type="image_path", converter=self.name)

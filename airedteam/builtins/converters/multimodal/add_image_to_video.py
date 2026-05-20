from __future__ import annotations

from pathlib import Path

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_video_manifest


class AddImageToVideoConverter:
    name = "add_image_to_video"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = output_dir

    async def convert(self, prompt: Prompt) -> Prompt:
        path = write_video_manifest(prompt.text, output_dir=self.output_dir, converter=self.name)
        return artifact_prompt(path, source=prompt, output_type="video_path", converter=self.name)

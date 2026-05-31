from __future__ import annotations

from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_wav_tone
from airedteam.core.types import Prompt


class AudioSpeedConverter:
    name = "audio_speed"

    def __init__(self, *, output_dir: str | Path | None = None, speed: float = 1.0) -> None:
        self.output_dir = output_dir
        self.speed = max(0.1, float(speed))

    async def convert(self, prompt: Prompt) -> Prompt:
        path = write_wav_tone(prompt.text, output_dir=self.output_dir, duration_s=0.5 / self.speed)
        return artifact_prompt(path, source=prompt, output_type="audio_path", converter=self.name)

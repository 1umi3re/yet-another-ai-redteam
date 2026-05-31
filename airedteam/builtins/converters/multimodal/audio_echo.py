from __future__ import annotations

from pathlib import Path

from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_wav_tone
from airedteam.core.types import Prompt


class AudioEchoConverter:
    name = "audio_echo"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = output_dir

    async def convert(self, prompt: Prompt) -> Prompt:
        path = write_wav_tone(prompt.text, output_dir=self.output_dir, duration_s=0.5)
        return artifact_prompt(path, source=prompt, output_type="audio_path", converter=self.name)

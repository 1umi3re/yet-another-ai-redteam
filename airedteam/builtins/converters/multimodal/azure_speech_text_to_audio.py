from __future__ import annotations

from pathlib import Path

from airedteam.core.types import Prompt
from airedteam.builtins.converters.support.artifact_utils import artifact_prompt, write_wav_tone


class AzureSpeechTextToAudioConverter:
    name = "azure_speech_text_to_audio"

    def __init__(self, *, output_dir: str | Path | None = None) -> None:
        self.output_dir = output_dir

    async def convert(self, prompt: Prompt) -> Prompt:
        path = write_wav_tone(prompt.text, output_dir=self.output_dir)
        return artifact_prompt(path, source=prompt, output_type="audio_path", converter=self.name)

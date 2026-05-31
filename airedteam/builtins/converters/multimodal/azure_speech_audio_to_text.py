from __future__ import annotations

from airedteam.core.types import Prompt


class AzureSpeechAudioToTextConverter:
    name = "azure_speech_audio_to_text"

    async def convert(self, prompt: Prompt) -> Prompt:
        metadata = dict(prompt.metadata)
        metadata.update(
            {
                "output_type": "text",
                "converter": self.name,
                "source_path": prompt.text,
            }
        )
        return Prompt(text=f"[audio transcription unavailable: {prompt.text}]", metadata=metadata)

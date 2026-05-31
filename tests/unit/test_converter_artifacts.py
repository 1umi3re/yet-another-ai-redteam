from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from airedteam.builtins.converters.multimodal.add_image_text import AddImageTextConverter
from airedteam.builtins.converters.multimodal.add_image_to_video import AddImageToVideoConverter
from airedteam.builtins.converters.multimodal.add_text_image import AddTextImageConverter
from airedteam.builtins.converters.multimodal.audio_echo import AudioEchoConverter
from airedteam.builtins.converters.multimodal.audio_frequency import AudioFrequencyConverter
from airedteam.builtins.converters.multimodal.audio_speed import AudioSpeedConverter
from airedteam.builtins.converters.multimodal.audio_volume import AudioVolumeConverter
from airedteam.builtins.converters.multimodal.audio_white_noise import AudioWhiteNoiseConverter
from airedteam.builtins.converters.multimodal.azure_speech_audio_to_text import (
    AzureSpeechAudioToTextConverter,
)
from airedteam.builtins.converters.multimodal.azure_speech_text_to_audio import (
    AzureSpeechTextToAudioConverter,
)
from airedteam.builtins.converters.multimodal.image_color_saturation import (
    ImageColorSaturationConverter,
)
from airedteam.builtins.converters.multimodal.image_compression import ImageCompressionConverter
from airedteam.builtins.converters.multimodal.image_noise import ImageNoiseConverter
from airedteam.builtins.converters.multimodal.image_resizing import ImageResizingConverter
from airedteam.builtins.converters.multimodal.image_rotation import ImageRotationConverter
from airedteam.builtins.converters.multimodal.pdf import PDFConverter
from airedteam.builtins.converters.multimodal.qr_code import QRCodeConverter
from airedteam.builtins.converters.multimodal.word_doc import WordDocConverter
from airedteam.builtins.converters.prompt_framing.indirect_web_pwn import IndirectWebPwnConverter
from airedteam.core.types import Prompt


def _assert_artifact(prompt: Prompt, suffix: str, output_type: str) -> Path:
    path = Path(prompt.text)
    assert path.exists()
    assert path.suffix == suffix
    assert prompt.metadata["output_type"] == output_type
    assert len(prompt.artifacts) == 1
    assert prompt.artifacts[0].path == str(path)
    return path


@pytest.mark.asyncio
async def test_document_artifact_converters(tmp_path):
    pdf = await PDFConverter(output_dir=tmp_path).convert(Prompt(text="hello pdf"))
    pdf_path = _assert_artifact(pdf, ".pdf", "binary_path")
    assert pdf.artifacts[0].kind == "binary"
    assert pdf.artifacts[0].media_type == "application/pdf"
    assert pdf_path.read_bytes().startswith(b"%PDF")

    doc = await WordDocConverter(output_dir=tmp_path).convert(Prompt(text="hello doc"))
    doc_path = _assert_artifact(doc, ".docx", "binary_path")
    with zipfile.ZipFile(doc_path) as archive:
        assert "word/document.xml" in archive.namelist()
        assert "hello doc" in archive.read("word/document.xml").decode()

    qr = await QRCodeConverter(output_dir=tmp_path).convert(Prompt(text="hello qr"))
    qr_path = _assert_artifact(qr, ".svg", "image_path")
    assert qr.artifacts[0].kind == "image"
    assert qr.artifacts[0].media_type == "image/svg+xml"
    assert "hello qr" in qr_path.read_text()


@pytest.mark.asyncio
async def test_image_artifact_converters(tmp_path):
    text_image = await AddTextImageConverter(output_dir=tmp_path).convert(Prompt(text="payload"))
    path = _assert_artifact(text_image, ".svg", "image_path")
    assert "payload" in path.read_text()

    for converter in (
        AddImageTextConverter(output_dir=tmp_path),
        ImageColorSaturationConverter(output_dir=tmp_path, saturation=0.5),
        ImageCompressionConverter(output_dir=tmp_path, quality=50),
        ImageNoiseConverter(output_dir=tmp_path, intensity=0.42),
        ImageResizingConverter(output_dir=tmp_path, width=320, height=200),
        ImageRotationConverter(output_dir=tmp_path, degrees=90),
    ):
        out = await converter.convert(Prompt(text="payload"))
        artifact = _assert_artifact(out, ".svg", "image_path")
        assert out.artifacts[0].kind == "image"
        assert converter.name in out.metadata["converter"]
        assert artifact.read_text()

    noisy = await ImageNoiseConverter(output_dir=tmp_path, intensity=0.42).convert(Prompt(text="payload"))
    noisy_svg = _assert_artifact(noisy, ".svg", "image_path").read_text()
    assert "feTurbulence" in noisy_svg
    assert "intensity=0.42" in noisy_svg


@pytest.mark.asyncio
async def test_audio_and_video_artifact_converters(tmp_path):
    for converter in (
        AzureSpeechTextToAudioConverter(output_dir=tmp_path),
        AudioEchoConverter(output_dir=tmp_path),
        AudioFrequencyConverter(output_dir=tmp_path, frequency_hz=440),
        AudioSpeedConverter(output_dir=tmp_path, speed=1.5),
        AudioVolumeConverter(output_dir=tmp_path, volume=0.5),
        AudioWhiteNoiseConverter(output_dir=tmp_path),
    ):
        out = await converter.convert(Prompt(text="speak"))
        artifact = _assert_artifact(out, ".wav", "audio_path")
        assert out.artifacts[0].kind == "audio"
        assert out.artifacts[0].media_type == "audio/wav"
        assert artifact.read_bytes().startswith(b"RIFF")

    video = await AddImageToVideoConverter(output_dir=tmp_path).convert(Prompt(text="scene"))
    video_path = _assert_artifact(video, ".json", "video_path")
    assert video.artifacts[0].kind == "video"
    payload = json.loads(video_path.read_text())
    assert payload["prompt"] == "scene"


@pytest.mark.asyncio
async def test_audio_to_text_converter_preserves_source_path(tmp_path):
    wav = tmp_path / "in.wav"
    wav.write_bytes(b"RIFF0000WAVE")
    out = await AzureSpeechAudioToTextConverter().convert(Prompt(text=str(wav)))
    assert out.text.startswith("[audio transcription unavailable:")
    assert out.metadata["output_type"] == "text"
    assert out.metadata["source_path"] == str(wav)


@pytest.mark.asyncio
async def test_promptfoo_multimodal_encoding_strategy_converters(tmp_path):
    audio = await AzureSpeechTextToAudioConverter(output_dir=tmp_path).convert(Prompt(text="payload"))
    audio_path = _assert_artifact(audio, ".wav", "audio_path")
    assert audio.artifacts[0].kind == "audio"
    assert audio_path.read_bytes().startswith(b"RIFF")

    image = await AddTextImageConverter(output_dir=tmp_path).convert(Prompt(text="payload"))
    image_path = _assert_artifact(image, ".svg", "image_path")
    assert image.artifacts[0].kind == "image"
    assert "payload" in image_path.read_text()

    video = await AddImageToVideoConverter(output_dir=tmp_path).convert(Prompt(text="payload"))
    video_path = _assert_artifact(video, ".json", "video_path")
    assert video.artifacts[0].kind == "video"
    assert json.loads(video_path.read_text())["prompt"] == "payload"


@pytest.mark.asyncio
async def test_promptfoo_indirect_web_pwn_converter_generates_html_artifact(tmp_path):
    out = await IndirectWebPwnConverter(output_dir=tmp_path, visible_task="Summarize this page").convert(
        Prompt(text="hidden browser instruction")
    )

    path = _assert_artifact(out, ".html", "binary_path")
    assert out.artifacts[0].kind == "binary"
    assert out.artifacts[0].media_type == "text/html"
    html = path.read_text()
    assert "Summarize this page" in html
    assert "hidden browser instruction" in html
    assert "display:none" in html

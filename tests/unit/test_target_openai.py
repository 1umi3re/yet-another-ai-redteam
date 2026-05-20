import json
import pytest
import respx
import httpx
from airedteam.builtins.targets.openai_compat import OpenAICompatNewSessionTarget, OpenAICompatTarget
from airedteam.core.types import Prompt, PromptArtifact


@pytest.mark.asyncio
@respx.mock
async def test_generate_returns_response():
    route = respx.post("https://api.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 2},
        })
    )
    t = OpenAICompatTarget(name="t1", base_url="https://api.example.com/v1", model="gpt-x", api_key="sk")
    r = await t.generate(Prompt(text="hi"))
    assert r.text == "ok"
    assert r.tokens_in == 5 and r.tokens_out == 2
    assert route.called
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_generate_raises_on_http_error():
    respx.post("https://api.example.com/v1/chat/completions").mock(return_value=httpx.Response(500, text="boom"))
    t = OpenAICompatTarget(name="t1", base_url="https://api.example.com/v1", model="m", api_key="k")
    with pytest.raises(Exception):
        await t.generate(Prompt(text="x"))
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_generate_preserves_system_prompt_and_temperature():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        })
    )
    t = OpenAICompatTarget(
        name="t", base_url="https://oai.example.com/v1", model="m", api_key="k",
        system_prompt="be helpful", temperature=0.7,
    )
    await t.generate(Prompt(text="hi"))
    body = json.loads(route.calls.last.request.content)
    assert body["temperature"] == 0.7
    assert body["messages"][0] == {"role": "system", "content": "be helpful"}
    assert body["messages"][-1] == {"role": "user", "content": "hi"}
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_generate_serializes_prompt_artifacts_as_multimodal_content(tmp_path):
    img = tmp_path / "prompt.svg"
    img.write_text("<svg>payload</svg>")
    wav = tmp_path / "prompt.wav"
    wav.write_bytes(b"RIFF0000WAVE")
    pdf = tmp_path / "prompt.pdf"
    pdf.write_bytes(b"%PDF-1.4 payload")

    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        })
    )
    t = OpenAICompatTarget(name="t", base_url="https://oai.example.com/v1", model="m", api_key="k")
    await t.generate(Prompt(
        text="converted artifact prompt",
        artifacts=[
            PromptArtifact(path=str(img), kind="image", media_type="image/svg+xml"),
            PromptArtifact(path=str(wav), kind="audio", media_type="audio/wav"),
            PromptArtifact(path=str(pdf), kind="binary", media_type="application/pdf"),
        ],
    ))

    body = json.loads(route.calls.last.request.content)
    content = body["messages"][-1]["content"]
    assert content[0] == {"type": "text", "text": "converted artifact prompt"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/svg+xml;base64,")
    assert content[2]["type"] == "input_audio"
    assert content[2]["input_audio"]["format"] == "wav"
    assert content[3]["type"] == "file"
    assert content[3]["file"]["filename"] == "prompt.pdf"
    assert content[3]["file"]["file_data"].startswith("data:application/pdf;base64,")
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_new_session_target_generate_adds_new_session_flag():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, json={
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        })
    )
    t = OpenAICompatNewSessionTarget(
        name="t", base_url="https://oai.example.com/v1", model="m", api_key="k",
    )
    await t.generate(Prompt(text="hi"))
    body = json.loads(route.calls.last.request.content)
    assert body["new_session"] is True
    assert body["messages"][-1] == {"role": "user", "content": "hi"}
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_check_stream_support_posts_stream_true():
    route = respx.post("https://oai.example.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=(
                b'data: {"choices":[{"delta":{"content":"o"}}]}\n\n'
                b'data: [DONE]\n\n'
            ),
        )
    )
    t = OpenAICompatTarget(name="t", base_url="https://oai.example.com/v1", model="m", api_key="k")
    ok, err = await t.check_stream_support(Prompt(text="ping"))
    body = json.loads(route.calls.last.request.content)
    assert ok is True
    assert err is None
    assert body["stream"] is True
    await t.aclose()

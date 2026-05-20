import json
import pytest
import respx
import httpx
from airedteam.builtins.targets.anthropic_compat import AnthropicCompatTarget
from airedteam.core.types import Prompt, PromptArtifact


@pytest.mark.asyncio
@respx.mock
async def test_generate():
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 4, "output_tokens": 1},
        })
    )
    t = AnthropicCompatTarget(name="a", base_url="https://api.anthropic.com/v1", model="claude-x", api_key="k", anthropic_version="2023-06-01", max_tokens=128)
    r = await t.generate(Prompt(text="hi"))
    assert r.text == "ok"
    assert r.tokens_in == 4 and r.tokens_out == 1
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_generate_preserves_system_prompt():
    route = respx.post("https://a.example.com/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        })
    )
    t = AnthropicCompatTarget(
        name="t", base_url="https://a.example.com/v1", model="m", api_key="k",
        system_prompt="be safe", max_tokens=32,
    )
    await t.generate(Prompt(text="hi"))
    body = json.loads(route.calls.last.request.content)
    assert body["system"] == "be safe"
    assert body["max_tokens"] == 32
    assert body["messages"] == [{"role": "user", "content": "hi"}]
    await t.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_generate_serializes_image_and_document_artifacts(tmp_path):
    img = tmp_path / "prompt.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\npayload")
    pdf = tmp_path / "prompt.pdf"
    pdf.write_bytes(b"%PDF-1.4 payload")

    route = respx.post("https://a.example.com/v1/messages").mock(
        return_value=httpx.Response(200, json={
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
        })
    )
    t = AnthropicCompatTarget(name="t", base_url="https://a.example.com/v1", model="m", api_key="k")
    await t.generate(Prompt(
        text="converted artifact prompt",
        artifacts=[
            PromptArtifact(path=str(img), kind="image", media_type="image/png"),
            PromptArtifact(path=str(pdf), kind="binary", media_type="application/pdf"),
        ],
    ))

    body = json.loads(route.calls.last.request.content)
    content = body["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "converted artifact prompt"}
    assert content[1]["type"] == "image"
    assert content[1]["source"]["media_type"] == "image/png"
    assert content[2]["type"] == "document"
    assert content[2]["source"]["media_type"] == "application/pdf"
    await t.aclose()

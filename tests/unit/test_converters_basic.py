import base64
import inspect

import pytest

from airedteam.builtins.converters.encoding.a1z26 import A1Z26Converter
from airedteam.builtins.converters.encoding.affine_cipher import AffineCipherConverter
from airedteam.builtins.converters.encoding.base64_conv import Base64Converter
from airedteam.builtins.converters.encoding.hex_conv import HexConverter
from airedteam.builtins.converters.encoding.hex_mixin import HexMixinConverter
from airedteam.builtins.converters.encoding.ogham import OghamConverter
from airedteam.builtins.converters.obfuscation.char_corrupt import CharCorruptConverter
from airedteam.builtins.converters.obfuscation.char_dropout import CharDropoutConverter
from airedteam.builtins.converters.obfuscation.word_mixin import WordMixinConverter
from airedteam.builtins.converters.prompt_framing.chain_of_thought import ChainOfThoughtConverter
from airedteam.builtins.converters.prompt_framing.job_role_generator import (
    JobRoleGeneratorConverter,
)
from airedteam.builtins.converters.prompt_framing.payload_mask_attack import (
    PayloadMaskAttackConverter,
)
from airedteam.builtins.converters.prompt_framing.sg_sentence_generator import (
    SGSentenceGeneratorConverter,
)
from airedteam.builtins.converters.utility.identity import IdentityConverter
from airedteam.core.types import Prompt


@pytest.mark.asyncio
async def test_identity():
    c = IdentityConverter()
    p = Prompt(text="hi")
    assert (await c.convert(p)).text == "hi"


@pytest.mark.asyncio
async def test_base64_raw_encodes():
    c = Base64Converter(wrap=False)
    out = await c.convert(Prompt(text="hello"))
    assert out.text == base64.b64encode(b"hello").decode()


@pytest.mark.asyncio
async def test_base64_default_wraps_with_instruction():
    c = Base64Converter()
    out = await c.convert(Prompt(text="hello"))
    assert "base64" in out.text.lower()
    assert base64.b64encode(b"hello").decode() in out.text


@pytest.mark.asyncio
async def test_base64_keeps_single_purpose_encoding_interface():
    assert "encoding_func" not in inspect.signature(Base64Converter).parameters
    assert (await HexConverter(wrap=False).convert(Prompt(text="hi"))).text == "68 69"


@pytest.mark.asyncio
async def test_a1z26_converter_encodes_letters_as_alphabet_positions():
    out = await A1Z26Converter(wrap=False).convert(Prompt(text="Ab z!"))

    assert out.text == "1-2 26!"


@pytest.mark.asyncio
async def test_affine_cipher_converter_encodes_letters_with_configured_keys():
    out = await AffineCipherConverter(a=5, b=8, wrap=False).convert(Prompt(text="attack AT"))

    assert out.text == "izzisg IZ"


@pytest.mark.asyncio
async def test_ogham_converter_maps_supported_letters_to_ogham_block():
    out = await OghamConverter(wrap=False).convert(Prompt(text="BAD!"))

    assert out.text == "\u1681\u1690\u1687!"


@pytest.mark.asyncio
async def test_char_dropout_removes_characters_with_deterministic_probability():
    out = await CharDropoutConverter(probability=1, seed=1).convert(Prompt(text="abcdef"))
    assert out.text == ""
    same = await CharDropoutConverter(probability=0, seed=1).convert(Prompt(text="abcdef"))
    assert same.text == "abcdef"


@pytest.mark.asyncio
async def test_char_corrupt_replaces_characters_with_configured_token():
    out = await CharCorruptConverter(probability=1, replacement="*-", seed=1).convert(Prompt(text="abc"))
    assert out.text == "*-*-*-"
    same = await CharCorruptConverter(probability=0, replacement="*-", seed=1).convert(Prompt(text="abc"))
    assert same.text == "abc"


@pytest.mark.asyncio
async def test_word_mixin_inserts_configured_words_periodically():
    out = await WordMixinConverter(words=["red"], every=2, seed=1).convert(Prompt(text="alpha beta gamma"))
    assert out.text == "alpha beta red gamma"


@pytest.mark.asyncio
async def test_hex_mixin_inserts_reproducible_hex_tokens_periodically():
    out = await HexMixinConverter(every=2, seed=1, digits=6).convert(Prompt(text="alpha beta gamma"))
    assert out.text.startswith("alpha beta {<")
    assert out.text.endswith("> } gamma") is False
    assert out.text.split()[2].startswith("{<")
    assert out.text.split()[2].endswith(">}")
    assert len(out.text.split()[2]) == len("{<000000>}")


@pytest.mark.asyncio
async def test_chain_of_thought_wraps_prompt_as_reasoning_request():
    out = await ChainOfThoughtConverter().convert(Prompt(text="explain the procedure"))
    assert "step by step" in out.text.lower()
    assert "explain the procedure" in out.text


@pytest.mark.asyncio
async def test_job_role_generator_adds_demographic_groups_to_role_prompt():
    out = await JobRoleGeneratorConverter(groups=["women", "older workers"]).convert(Prompt(text="software engineer"))

    assert "software engineer" in out.text
    assert "women" in out.text
    assert "older workers" in out.text
    assert "job role" in out.text.lower()


@pytest.mark.asyncio
async def test_payload_mask_attack_masks_configured_word_positions():
    out = await PayloadMaskAttackConverter(mask_token="[MASK]", every=2).convert(Prompt(text="write a safe report"))

    assert "write [MASK] safe [MASK]" in out.text
    assert "fill in" in out.text.lower()


@pytest.mark.asyncio
async def test_sg_sentence_generator_frames_seed_as_singlish_completion():
    out = await SGSentenceGeneratorConverter(slang_suffix="lah").convert(Prompt(text="Complete this warning"))

    assert "Singapore" in out.text
    assert "Singlish" in out.text
    assert "Complete this warning" in out.text
    assert out.text.endswith("lah")

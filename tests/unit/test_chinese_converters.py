from __future__ import annotations

import pytest

from airedteam.core.plugins import BaseTarget
from airedteam.core.types import Prompt, Response


class FakeChineseRewriter(BaseTarget):
    name = "fake_chinese_rewriter"

    def __init__(self, out: str = "改写结果") -> None:
        self.out = out
        self.seen: list[str] = []

    async def generate(self, prompt: Prompt) -> Response:
        self.seen.append(prompt.text)
        return Response(text=self.out, raw={}, latency_ms=1)

    async def aclose(self) -> None:
        pass


@pytest.mark.asyncio
async def test_chinese_phonetic_converters_transform_hanzi():
    from airedteam.builtins.converters.encoding.zh_pinyin import ZhPinyinConverter
    from airedteam.builtins.converters.encoding.zh_pinyin_initials import ZhPinyinInitialsConverter
    from airedteam.builtins.converters.encoding.zh_zhuyin import ZhZhuyinConverter

    prompt = Prompt(text="测试中文ABC")

    pinyin = await ZhPinyinConverter(tone="number", separator="-").convert(prompt)
    assert pinyin.text == "ce4-shi4-zhong1-wen2-A-B-C"

    initials = await ZhPinyinInitialsConverter(separator="").convert(prompt)
    assert initials.text == "cszwABC"

    zhuyin = await ZhZhuyinConverter(separator=" ").convert(Prompt(text="中文"))
    assert zhuyin.text == "ㄓㄨㄥ ㄨㄣˊ"


@pytest.mark.asyncio
async def test_chinese_script_and_surface_obfuscation_converters_are_deterministic():
    from airedteam.builtins.converters.encoding.zh_fullwidth import ZhFullwidthConverter
    from airedteam.builtins.converters.encoding.zh_homophone import ZhHomophoneConverter
    from airedteam.builtins.converters.encoding.zh_mars_text import ZhMarsTextConverter
    from airedteam.builtins.converters.encoding.zh_mixed_notation import ZhMixedNotationConverter
    from airedteam.builtins.converters.encoding.zh_number_homophone import ZhNumberHomophoneConverter
    from airedteam.builtins.converters.encoding.zh_punctuation_noise import ZhPunctuationNoiseConverter
    from airedteam.builtins.converters.encoding.zh_rare_variant import ZhRareVariantConverter
    from airedteam.builtins.converters.encoding.zh_simplified_traditional import (
        ZhSimplifiedTraditionalConverter,
    )
    from airedteam.builtins.converters.encoding.zh_unicode_compat import ZhUnicodeCompatConverter

    assert (await ZhSimplifiedTraditionalConverter(direction="s2t").convert(Prompt(text="汉语测试"))).text == "漢語測試"
    assert (await ZhRareVariantConverter(probability=1, seed="1").convert(Prompt(text="汉语龙云"))).text != "汉语龙云"
    assert (await ZhHomophoneConverter(probability=1, seed="1").convert(Prompt(text="测试"))).text != "测试"
    assert (await ZhNumberHomophoneConverter().convert(Prompt(text="一生一起"))).text == "1生17"
    assert (await ZhMarsTextConverter(seed="1").convert(Prompt(text="测试ABC"))).text != "测试ABC"
    assert (await ZhFullwidthConverter().convert(Prompt(text="ABC 123,测试"))).text == "ＡＢＣ　１２３，测试"
    assert (await ZhPunctuationNoiseConverter(mark="·", every=1).convert(Prompt(text="测试ABC"))).text == "测·试·ABC"
    assert (await ZhUnicodeCompatConverter(probability=1, seed="1").convert(Prompt(text="一二三"))).text != "一二三"

    mixed = await ZhMixedNotationConverter(mode="pinyin", probability=1, seed="1").convert(Prompt(text="中文"))
    assert mixed.text == "zhong wen"


@pytest.mark.asyncio
async def test_chinese_decomposition_converters_wrap_reassembly_context():
    from airedteam.builtins.converters.encoding.zh_stroke_code import ZhStrokeCodeConverter
    from airedteam.builtins.converters.prompt_framing.zh_ids_decomposition import ZhIdsDecompositionConverter
    from airedteam.builtins.converters.prompt_framing.zh_radical_split import ZhRadicalSplitConverter

    radical = await ZhRadicalSplitConverter().convert(Prompt(text="明好"))
    assert "日+月" in radical.text
    assert "女+子" in radical.text
    assert "重组" in radical.text

    ids = await ZhIdsDecompositionConverter().convert(Prompt(text="明好"))
    assert "⿰日月" in ids.text
    assert "⿰女子" in ids.text

    stroke = await ZhStrokeCodeConverter().convert(Prompt(text="一二三"))
    assert "一:1" in stroke.text
    assert "二:2" in stroke.text
    assert "三:3" in stroke.text


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("module_name", "class_name", "needle"),
    [
        ("zh_classical_chinese", "ZhClassicalChineseConverter", "文言"),
        ("zh_dialect_rewrite", "ZhDialectRewriteConverter", "粤语"),
        ("zh_net_slang", "ZhNetSlangConverter", "网络黑话"),
        ("zh_idiom_allusion", "ZhIdiomAllusionConverter", "成语"),
        ("zh_poetic_rewrite", "ZhPoeticRewriteConverter", "诗词"),
        ("zh_bureaucratic_style", "ZhBureaucraticStyleConverter", "公文"),
        ("zh_code_switch", "ZhCodeSwitchConverter", "中英"),
    ],
)
async def test_chinese_llm_rewrite_converters_call_helper_llm(module_name, class_name, needle):
    module = __import__(f"airedteam.builtins.converters.llm_rewrite.{module_name}", fromlist=[class_name])
    converter_cls = getattr(module, class_name)
    helper = FakeChineseRewriter("只返回改写文本")

    out = await converter_cls(converter=helper).convert(Prompt(text="测试中文目标"))

    assert out.text == "只返回改写文本"
    assert helper.seen
    assert "测试中文目标" in helper.seen[0]
    assert needle in helper.seen[0]
    assert "只返回改写后的 prompt" in helper.seen[0]


def test_chinese_llm_rewrite_converters_require_helper_llm():
    from airedteam.builtins.converters.llm_rewrite.zh_classical_chinese import (
        ZhClassicalChineseConverter,
    )

    with pytest.raises(ValueError, match="converter_config_id"):
        ZhClassicalChineseConverter(converter=None)

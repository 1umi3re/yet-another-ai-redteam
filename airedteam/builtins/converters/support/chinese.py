from __future__ import annotations

import random
import re
from collections.abc import Callable

from airedteam.builtins.converters.support.template_helpers import converted_prompt
from airedteam.core.types import Prompt


def parse_probability(value: float | str | None, default: float = 0.5) -> float:
    try:
        probability = float(default if value is None or value == "" else value)
    except (TypeError, ValueError):
        probability = default
    return max(0.0, min(1.0, probability))


def parse_every(value: int | str | None, default: int = 1) -> int:
    try:
        every = int(default if value is None or value == "" else value)
    except (TypeError, ValueError):
        every = default
    return max(1, every)


def rng_from_seed(seed: str | int | None) -> random.Random:
    return random.Random(str(seed or "0"))


def is_cjk(char: str) -> bool:
    return "\u3400" <= char <= "\u9fff" or "\uf900" <= char <= "\ufaff"


def maybe_replace_chars(
    text: str,
    mapping: dict[str, str | list[str]],
    *,
    probability: float | str | None = 1.0,
    seed: str | int | None = None,
) -> str:
    rng = rng_from_seed(seed)
    threshold = parse_probability(probability, default=1.0)
    out: list[str] = []
    for char in text:
        replacement = mapping.get(char)
        if replacement is None or rng.random() > threshold:
            out.append(char)
            continue
        if isinstance(replacement, list):
            out.append(rng.choice(replacement))
        else:
            out.append(replacement)
    return "".join(out)


def greedy_replace(text: str, mapping: dict[str, str]) -> str:
    keys = sorted(mapping, key=len, reverse=True)
    out: list[str] = []
    index = 0
    while index < len(text):
        matched = False
        for key in keys:
            if text.startswith(key, index):
                out.append(mapping[key])
                index += len(key)
                matched = True
                break
        if not matched:
            out.append(text[index])
            index += 1
    return "".join(out)


def fullwidth_text(text: str) -> str:
    out: list[str] = []
    for char in text:
        code = ord(char)
        if char == " ":
            out.append("\u3000")
        elif 0x21 <= code <= 0x7E:
            out.append(chr(code + 0xFEE0))
        else:
            out.append(char)
    return "".join(out)


def pinyin_tokens(text: str, *, tone: str = "number") -> list[str]:
    from pypinyin import Style, lazy_pinyin

    style = {
        "none": Style.NORMAL,
        "number": Style.TONE3,
        "marks": Style.TONE,
    }.get(tone, Style.TONE3)
    return lazy_pinyin(text, style=style, neutral_tone_with_five=True, errors=lambda item: list(item))


def zhuyin_tokens(text: str) -> list[str]:
    from pypinyin import Style, lazy_pinyin

    return lazy_pinyin(text, style=Style.BOPOMOFO, errors=lambda item: list(item))


def pinyin_initial_tokens(text: str) -> list[str]:
    from pypinyin import Style, lazy_pinyin

    return lazy_pinyin(text, style=Style.FIRST_LETTER, errors=lambda item: list(item))


def opencc_convert(text: str, direction: str) -> str:
    from opencc import OpenCC

    configs = {
        "s2t": "s2t",
        "t2s": "t2s",
        "s2tw": "s2tw",
        "s2hk": "s2hk",
        "t2tw": "t2tw",
        "t2hk": "t2hk",
    }
    converter = OpenCC(configs.get(direction, "s2t"))
    return converter.convert(text)


def join_tokens(tokens: list[str], separator: str) -> str:
    return "".join(tokens) if separator == "" else separator.join(tokens)


def cjk_token_transform(text: str, transform: Callable[[str], str], separator: str) -> str:
    tokens: list[str] = []
    pending_cjk: list[str] = []

    def flush_cjk() -> None:
        if not pending_cjk:
            return
        tokens.extend(transform(char) for char in pending_cjk)
        pending_cjk.clear()

    for char in text:
        if is_cjk(char):
            pending_cjk.append(char)
        else:
            flush_cjk()
            tokens.append(char)
    flush_cjk()
    return join_tokens(tokens, separator)


def wrap_decode_instruction(prompt: Prompt, text: str, *, enabled: bool, label: str) -> Prompt:
    if not enabled:
        return converted_prompt(prompt, text)
    return converted_prompt(prompt, f"请先还原或重组以下{label}文本，再理解并完成其中的请求：\n{text}")


RARE_VARIANT_MAP = {
    "一": "壹",
    "二": "贰",
    "三": "叁",
    "万": "萬",
    "与": "與",
    "云": "雲",
    "为": "爲",
    "汉": "漢",
    "语": "語",
    "龙": "龍",
    "马": "馬",
    "门": "門",
    "风": "風",
}

HOMOPHONE_MAP = {
    "ce": ["策"],
    "shi": ["式", "市"],
    "zhong": ["钟", "忠"],
    "wen": ["闻"],
    "han": ["函"],
    "yu": ["雨", "域"],
    "long": ["隆"],
    "yun": ["运"],
}

NUMBER_HOMOPHONE_MAP = {
    "一起": "17",
    "一世": "14",
    "拜拜": "88",
    "不要": "81",
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
    "零": "0",
}

MARS_TEXT_MAP = {
    **RARE_VARIANT_MAP,
    "测": "測",
    "试": "試",
    "中": "狆",
    "文": "呅",
    "的": "嘚",
    "是": "媞",
    "你": "妳",
    "我": "偶",
    "么": "庅",
}

UNICODE_COMPAT_MAP = {
    "一": "\uf9dc",
    "二": "\u3192",
    "三": "\u3193",
    "人": "\uf9fd",
    "力": "\uf98a",
    "女": "\uf981",
    "子": "\uf9d0",
    "日": "\uf9e5",
    "月": "\uf9d4",
}

RADICAL_SPLIT_MAP = {
    "明": "日+月",
    "好": "女+子",
    "休": "亻+木",
    "信": "亻+言",
    "林": "木+木",
    "森": "木+木+木",
    "问": "门+口",
    "闻": "门+耳",
    "语": "讠+吾",
}

IDS_MAP = {
    "明": "⿰日月",
    "好": "⿰女子",
    "休": "⿰亻木",
    "信": "⿰亻言",
    "林": "⿰木木",
    "森": "⿱木林",
    "问": "⿵门口",
    "闻": "⿵门耳",
    "语": "⿰讠吾",
}

STROKE_COUNT_MAP = {
    "一": 1,
    "二": 2,
    "三": 3,
    "人": 2,
    "口": 3,
    "女": 3,
    "子": 3,
    "中": 4,
    "文": 4,
    "日": 4,
    "月": 4,
    "明": 8,
    "好": 6,
    "汉": 5,
    "語": 14,
    "语": 9,
}


def split_cjk_and_other(text: str) -> list[str]:
    return re.findall(r"[\u3400-\u9fff\uf900-\ufaff]|[^\u3400-\u9fff\uf900-\ufaff]+", text)

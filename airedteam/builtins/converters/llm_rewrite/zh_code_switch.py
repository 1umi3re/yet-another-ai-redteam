from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhCodeSwitchConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts with Chinese-English or Chinese-Pinyin code switching."""

    name = "zh_code_switch"
    default_style = "中英夹杂/中文拼音混写"
    default_prompt_asset_id = "zh_code_switch.rewrite.v1"

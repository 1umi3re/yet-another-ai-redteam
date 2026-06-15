from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhBureaucraticStyleConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts into bureaucratic or formal document style."""

    name = "zh_bureaucratic_style"
    default_style = "中文公文/正式报告语体"
    default_prompt_asset_id = "zh_bureaucratic_style.rewrite.v1"

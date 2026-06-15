from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhClassicalChineseConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts into classical or semi-classical Chinese."""

    name = "zh_classical_chinese"
    default_style = "文言/半文言"
    default_prompt_asset_id = "zh_classical_chinese.rewrite.v1"

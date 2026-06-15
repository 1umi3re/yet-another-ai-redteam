from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhDialectRewriteConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts into a configured Chinese dialect style."""

    name = "zh_dialect_rewrite"
    default_style = "粤语口语"
    default_prompt_asset_id = "zh_dialect_rewrite.rewrite.v1"

from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhIdiomAllusionConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts through idioms, allusions, and metaphor."""

    name = "zh_idiom_allusion"
    default_style = "成语典故和隐喻"
    default_prompt_asset_id = "zh_idiom_allusion.rewrite.v1"

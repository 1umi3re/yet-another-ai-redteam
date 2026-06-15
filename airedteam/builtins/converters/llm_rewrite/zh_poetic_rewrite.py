from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhPoeticRewriteConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts as poetic Chinese expression."""

    name = "zh_poetic_rewrite"
    default_style = "诗词化中文"
    default_prompt_asset_id = "zh_poetic_rewrite.rewrite.v1"

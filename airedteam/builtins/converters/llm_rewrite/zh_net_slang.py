from __future__ import annotations

from airedteam.builtins.converters.llm_rewrite.zh_style_rewrite import ChineseStyleRewriteConverter


class ZhNetSlangConverter(ChineseStyleRewriteConverter):
    """Rewrite Chinese prompts using Chinese internet slang and coded phrasing."""

    name = "zh_net_slang"
    default_style = "中文网络黑话"
    default_prompt_asset_id = "zh_net_slang.rewrite.v1"

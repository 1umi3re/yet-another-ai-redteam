import json
from pathlib import Path

LLM_REWRITE_ASSETS = {
    "llm_variation": "llm_variation.rewrite.v1",
    "llm_tone": "llm_tone.rewrite.v1",
    "llm_persuasion": "llm_persuasion.rewrite.v1",
    "llm_generic": "llm_generic.rewrite.v1",
    "llm_malicious_question": "llm_malicious_question.rewrite.v1",
    "llm_toxic_sentence": "llm_toxic_sentence.rewrite.v1",
    "llm_random_translation": "llm_random_translation.rewrite.v1",
    "llm_scientific_translation": "llm_scientific_translation.rewrite.v1",
    "translation_llm": "translation_llm.translate.v1",
    "low_resource_language": "low_resource_language.translate.v1",
    "multilingual": "multilingual.translate.v1",
    "paraphrase_fast": "paraphrase_fast.rewrite.v1",
    "paraphrase_pegasus": "paraphrase_pegasus.rewrite.v1",
    "tense": "tense.rewrite.v1",
    "meta_agent": "meta_agent.rewrite.v1",
    "zh_classical_chinese": "zh_classical_chinese.rewrite.v1",
    "zh_dialect_rewrite": "zh_dialect_rewrite.rewrite.v1",
    "zh_net_slang": "zh_net_slang.rewrite.v1",
    "zh_idiom_allusion": "zh_idiom_allusion.rewrite.v1",
    "zh_poetic_rewrite": "zh_poetic_rewrite.rewrite.v1",
    "zh_bureaucratic_style": "zh_bureaucratic_style.rewrite.v1",
    "zh_code_switch": "zh_code_switch.rewrite.v1",
}

CHINESE_REWRITE_KEYWORDS = {
    "zh_classical_chinese": ["文言", "半文言", "现代口语"],
    "zh_dialect_rewrite": ["方言", "地域口语", "粤语"],
    "zh_net_slang": ["网络黑话", "缩写", "梗"],
    "zh_idiom_allusion": ["成语", "典故", "隐喻"],
    "zh_poetic_rewrite": ["诗词", "意象", "韵律"],
    "zh_bureaucratic_style": ["公文", "报告", "条款"],
    "zh_code_switch": ["中英夹杂", "code-switch", "拼音"],
}


def _converter_assets_by_id() -> dict[str, dict]:
    path = Path("airedteam/builtins/prompt_assets/converter_prompt_assets.json")
    return {item["id"]: item for item in json.loads(path.read_text())}


def test_all_llm_rewrite_methods_have_converter_prompt_assets():
    assets = _converter_assets_by_id()

    for plugin, asset_id in LLM_REWRITE_ASSETS.items():
        asset = assets[asset_id]
        assert asset["plugin"] == plugin
        assert asset["purpose"] == "converter_prompt"
        assert "prompt" in asset["variables"]
        assert "{prompt}" in asset["template"]


def test_chinese_llm_rewrite_templates_are_method_specific():
    assets = _converter_assets_by_id()
    templates = {
        plugin: assets[asset_id]["template"]
        for plugin, asset_id in LLM_REWRITE_ASSETS.items()
        if plugin.startswith("zh_")
    }

    assert len(set(templates.values())) == len(templates)
    for plugin, keywords in CHINESE_REWRITE_KEYWORDS.items():
        template = templates[plugin]
        missing = [keyword for keyword in keywords if keyword not in template]
        assert not missing, f"{plugin} template missing method-specific keywords: {missing}"

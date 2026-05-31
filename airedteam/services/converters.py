from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from airedteam.core.types import Prompt
from airedteam.engine.factory import build_converter, build_target

_LLM_CONVERTERS = {
    "llm_variation",
    "llm_tone",
    "llm_persuasion",
    "llm_generic",
    "tense",
    "llm_malicious_question",
    "llm_toxic_sentence",
    "llm_random_translation",
    "llm_scientific_translation",
    "paraphrase_fast",
    "paraphrase_pegasus",
    "meta_agent",
}

_TRANSLATION_CONVERTERS = {
    "translation_llm",
    "low_resource_language",
    "multilingual",
}


@dataclass(frozen=True)
class ConverterPreview:
    original_text: str
    transformed_text: str
    converter_chain: list[str]
    converters: list[dict[str, Any]]


class ConverterChainService:
    def __init__(self, target_configs, prompt_assets=None) -> None:
        self._targets = target_configs
        self._prompt_assets = prompt_assets

    async def _resolve_attack_template(self, params: dict[str, Any]) -> None:
        if self._prompt_assets is None or not params.get("attack_template_asset_id"):
            return
        asset_id = params.pop("attack_template_asset_id")
        asset = await self._prompt_assets.get_asset(asset_id)
        if asset.get("purpose") != "attack_template":
            raise ValueError(f"prompt asset is not an attack template: {asset_id}")
        active_override = asset.get("active_override")
        params["template"] = (
            active_override.get("template")
            if isinstance(active_override, dict) and active_override.get("template")
            else asset["template"]
        )

    async def apply(self, text: str, refs: list[dict[str, Any]] | None) -> ConverterPreview:
        refs = refs or []
        prompt = Prompt(text=text)
        chain: list[str] = []
        closeables = []
        converters = []
        try:
            for ref in refs:
                plugin = ref.get("plugin")
                if not plugin:
                    raise ValueError(f"converter ref missing 'plugin': {ref}")
                params = dict(ref.get("params") or {})
                if plugin in _TRANSLATION_CONVERTERS and "translator_config_id" in params:
                    translator_id = params.pop("translator_config_id")
                    target_cfg = await self._targets.resolve_for_runtime(translator_id)
                    translator = build_target(target_cfg)
                    closeables.append(translator)
                    params["translator"] = translator
                if plugin in _LLM_CONVERTERS and "converter_config_id" in params:
                    converter_id = params.pop("converter_config_id")
                    target_cfg = await self._targets.resolve_for_runtime(converter_id)
                    converter_target = build_target(target_cfg)
                    closeables.append(converter_target)
                    params["converter"] = converter_target
                if plugin in _LLM_CONVERTERS or plugin in _TRANSLATION_CONVERTERS:
                    params["prompt_assets"] = self._prompt_assets
                if plugin == "template_jailbreak":
                    await self._resolve_attack_template(params)
                converter = build_converter({"plugin": plugin, "params": params})
                converters.append(
                    {
                        "plugin": plugin,
                        "params": dict(ref.get("params") or {}),
                    }
                )
                prompt = await converter.convert(prompt)
                chain.append(converter.name)
        finally:
            for target in closeables:
                await target.aclose()
        return ConverterPreview(
            original_text=text,
            transformed_text=prompt.text,
            converter_chain=chain,
            converters=converters,
        )

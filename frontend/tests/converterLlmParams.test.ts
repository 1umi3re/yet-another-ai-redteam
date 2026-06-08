import assert from "node:assert/strict";
import test from "node:test";

import {
  applyConverterLlmConfig,
  countConvertersWithLlmConfig,
  getConverterLlmParamKeys,
} from "../src/lib/converterLlmParams.js";

const schemas = {
  llm_variation: {
    converter_config_id: { type: "target_ref", required: true, label: "Converter LLM" },
    instructions: { type: "text", default: "", label: "Instructions" },
  },
  translation_llm: {
    translator_config_id: { type: "target_ref", required: true, label: "Translator LLM" },
    target_language: { type: "string", default: "French", label: "Target language" },
  },
  base64: {
    wrap: { type: "bool", default: true, label: "Wrap with decode instruction" },
  },
} as const;

test("detects converter LLM params in selected converter schemas", () => {
  assert.deepEqual(getConverterLlmParamKeys("llm_variation", schemas), ["converter_config_id"]);
  assert.deepEqual(getConverterLlmParamKeys("translation_llm", schemas), ["translator_config_id"]);
  assert.deepEqual(getConverterLlmParamKeys("base64", schemas), []);
});

test("applies one helper LLM config to every selected converter that requires it", () => {
  const converters = [
    { plugin: "llm_variation", params: { instructions: "preserve intent" } },
    { plugin: "translation_llm", params: { target_language: "Spanish" } },
    { plugin: "base64", params: { wrap: false } },
  ];

  const updated = applyConverterLlmConfig(converters, schemas, "helper-target");

  assert.deepEqual(updated, [
    {
      plugin: "llm_variation",
      params: { converter_config_id: "helper-target", instructions: "preserve intent" },
    },
    {
      plugin: "translation_llm",
      params: { translator_config_id: "helper-target", target_language: "Spanish" },
    },
    { plugin: "base64", params: { wrap: false } },
  ]);
  assert.equal(countConvertersWithLlmConfig(converters, schemas), 2);
});

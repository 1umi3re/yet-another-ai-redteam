import assert from "node:assert/strict";
import test from "node:test";

import {
  buildConverterAttackCategoryState,
  filterMappings,
  formatAttackMethodName,
  mappingKey,
  scopeMappings,
  sortCategories,
} from "../src/lib/attackMethodTaxonomy.js";

const categories = [
  { id: "later", name: "Later", alias: "Later", type: "custom", display_order: 20 },
  { id: "first", name: "First", alias: "Primary", type: "builtin", display_order: 10 },
];

const mappings = [
  { executor_kind: "executor" as const, executor_name: "single_turn", category_id: "first", technical_category: "executor" },
  { executor_kind: "converter_method" as const, executor_name: "base64", category_id: "later", technical_category: "encoding" },
  { executor_kind: "converter_method" as const, executor_name: "orphan", category_id: "missing", technical_category: "other" },
];

test("sortCategories orders by display_order then name", () => {
  assert.deepEqual(sortCategories(categories).map(category => category.id), ["first", "later"]);
});

test("scopeMappings filters all, uncategorized, and category scopes", () => {
  const categoryById = new Map(categories.map(category => [category.id, category]));
  assert.equal(scopeMappings(mappings, categoryById, { kind: "all" }).length, 3);
  assert.deepEqual(
    scopeMappings(mappings, categoryById, { kind: "uncategorized" }).map(mapping => mapping.executor_name),
    ["orphan"],
  );
  assert.deepEqual(
    scopeMappings(mappings, categoryById, { kind: "category", id: "later" }).map(mapping => mapping.executor_name),
    ["base64"],
  );
});

test("filterMappings searches within the scoped set and respects kind", () => {
  const categoryById = new Map(categories.map(category => [category.id, category]));
  assert.deepEqual(
    filterMappings(mappings, categoryById, "primary", "all").map(mapping => mapping.executor_name),
    ["single_turn"],
  );
  assert.deepEqual(
    filterMappings(mappings, categoryById, "", "converter_method").map(mapping => mapping.executor_name),
    ["base64", "orphan"],
  );
});

test("mappingKey is stable for batch selection", () => {
  assert.equal(mappingKey(mappings[1]), "converter_method:base64");
});

test("formatAttackMethodName localizes known method names and preserves proper nouns", () => {
  assert.equal(formatAttackMethodName("single_turn", "zh"), "单轮攻击");
  assert.equal(formatAttackMethodName("base64", "zh"), "Base64 编码");
  assert.equal(formatAttackMethodName("dan", "zh"), "DAN");
  assert.equal(formatAttackMethodName("crescendo", "zh"), "Crescendo");
  assert.equal(formatAttackMethodName("single_turn", "en"), "single_turn");
  assert.equal(formatAttackMethodName("unknown_plugin", "zh"), "unknown_plugin");
});

test("buildConverterAttackCategoryState groups converters by attack_method categories", () => {
  const state = buildConverterAttackCategoryState({
    availableConverters: ["prefix", "base64", "dan", "unknown"],
    selectedConverters: ["dan"],
    attackCategories: {
      prefix: "instruction_override",
      base64: "encoding_obfuscation",
      dan: "role_play_persona",
    },
    categoryMeta: {
      role_play_persona: {
        id: "role_play_persona",
        name: "角色扮演",
        alias: "role-play / persona",
        display_order: 3,
      },
      instruction_override: {
        id: "instruction_override",
        name: "指令覆盖",
        alias: "instruction override",
        display_order: 1,
      },
      encoding_obfuscation: {
        id: "encoding_obfuscation",
        name: "编码 / 混淆",
        alias: "encoding / obfuscation",
        display_order: 14,
      },
    },
  });

  assert.deepEqual(state.options, [
    "all",
    "selected",
    "instruction_override",
    "role_play_persona",
    "encoding_obfuscation",
    "uncategorized",
  ]);
  assert.equal(state.counts.all, 4);
  assert.equal(state.counts.selected, 1);
  assert.equal(state.counts.encoding_obfuscation, 1);
  assert.equal(state.categoryFor("unknown"), "uncategorized");
  assert.equal(state.labelFor("base64"), "编码 / 混淆");
  assert.equal(state.labelForCategory("selected"), "Selected");
});

import assert from "node:assert/strict";
import test from "node:test";

import {
  filterMappings,
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

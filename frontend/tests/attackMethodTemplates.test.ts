import assert from "node:assert/strict";
import test from "node:test";

import {
  expandConverterWithAttackTemplates,
  expandRunSpecAttackTemplates,
} from "../src/lib/attackMethodTemplates.js";

test("expandConverterWithAttackTemplates creates one converter ref per method template", () => {
  const expanded = expandConverterWithAttackTemplates(
    { plugin: "dan", params: { persona: "auditor" } },
    {
      is_template_backed: true,
      default_asset_id: "attack_method.dan.default.v1",
      templates: [
        { id: "builtin", asset_id: "attack_method.dan.default.v1", is_builtin: true },
        { id: "attack_method.dan.template.superior_dan.v1", asset_id: "attack_method.dan.template.superior_dan.v1", is_builtin: true },
        { id: "override-1", asset_id: "attack_method.dan.default.v1", is_builtin: false },
      ],
    },
  );

  assert.deepEqual(expanded, [
    {
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.default.v1",
        attack_template_use_builtin: true,
      },
    },
    {
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.template.superior_dan.v1",
        attack_template_use_builtin: true,
      },
    },
    {
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.default.v1",
        attack_template_override_id: "override-1",
      },
    },
  ]);
});

test("expandConverterWithAttackTemplates keeps non-template-backed methods unchanged", () => {
  assert.deepEqual(
    expandConverterWithAttackTemplates(
      { plugin: "base64", params: { wrap: false } },
      { is_template_backed: false, default_asset_id: null, templates: [] },
    ),
    [{ plugin: "base64", params: { wrap: false } }],
  );
});

test("expandRunSpecAttackTemplates expands legacy preset converters", async () => {
  const runspec = {
    version: 1,
    converters: [
      { plugin: "dan", params: { persona: "auditor" } },
      { plugin: "base64", params: { wrap: false } },
    ],
    executor: { plugin: "single_turn" },
  };

  const expanded = await expandRunSpecAttackTemplates(runspec, async plugin => (
    plugin === "dan"
      ? {
        is_template_backed: true,
        default_asset_id: "attack_method.dan.default.v1",
        templates: [
          { id: "builtin", asset_id: "attack_method.dan.default.v1", is_builtin: true },
          { id: "override-1", asset_id: "attack_method.dan.default.v1", is_builtin: false },
        ],
      }
      : { is_template_backed: false, default_asset_id: null, templates: [] }
  ));

  assert.deepEqual(expanded.converters, [
    {
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.default.v1",
        attack_template_use_builtin: true,
      },
    },
    {
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.default.v1",
        attack_template_override_id: "override-1",
      },
    },
    { plugin: "base64", params: { wrap: false } },
  ]);
  assert.deepEqual(runspec.converters[0], { plugin: "dan", params: { persona: "auditor" } });
});

test("expandRunSpecAttackTemplates expands converter-method executor refs", async () => {
  const expanded = await expandRunSpecAttackTemplates(
    {
      version: 2,
      executors: [
        { kind: "executor", plugin: "single_turn", params: {} },
        { kind: "converter_method", plugin: "dan", params: { persona: "auditor" } },
      ],
    },
    async () => ({
      is_template_backed: true,
      default_asset_id: "attack_method.dan.default.v1",
      templates: [
        { id: "builtin", asset_id: "attack_method.dan.default.v1", is_builtin: true },
        { id: "override-1", asset_id: "attack_method.dan.default.v1", is_builtin: false },
      ],
    }),
  );

  assert.deepEqual(expanded.executors, [
    { kind: "executor", plugin: "single_turn", params: {} },
    {
      kind: "converter_method",
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.default.v1",
        attack_template_use_builtin: true,
      },
    },
    {
      kind: "converter_method",
      plugin: "dan",
      params: {
        persona: "auditor",
        attack_template_asset_id: "attack_method.dan.default.v1",
        attack_template_override_id: "override-1",
      },
    },
  ]);
});

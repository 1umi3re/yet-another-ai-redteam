import assert from "node:assert/strict";
import test from "node:test";

import { expandConverterWithAttackTemplates } from "../src/lib/attackMethodTemplates.js";

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

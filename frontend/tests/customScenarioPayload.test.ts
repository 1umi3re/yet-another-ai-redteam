import assert from "node:assert/strict";
import test from "node:test";

import { buildCustomScenarioPayload } from "../src/lib/customScenarioPayload.js";

test("buildCustomScenarioPayload stores pipeline without target or dataset bindings", () => {
  const payload = buildCustomScenarioPayload({
    scenarioName: "Saved pipeline",
    description: "Reusable pipeline",
    tagsText: "custom, regression",
    nativeExecutors: [
      { kind: "executor", plugin: "single_turn", params: {} },
      { kind: "executor", plugin: "general_multi_turn", params: { goal: "Use dataset item", rounds: 3 } },
    ],
    converters: [{ plugin: "base64", params: { wrap: false } }],
    scorer: { plugin: "refusal", params: {} },
    generalMultiTurnExecutors: ["general_multi_turn"],
    goalSource: "dataset_items",
    samplingEnabled: true,
    samplingLimit: "25",
    samplingShuffle: true,
    samplingSeed: "42",
    timeoutSeconds: "120",
  });

  assert.equal(payload.name, "Saved pipeline");
  assert.equal(payload.description, "Reusable pipeline");
  assert.deepEqual(payload.tags, ["custom", "regression"]);
  assert.deepEqual(payload.template, {
    version: 2,
    executors: [
      { kind: "executor", plugin: "single_turn", params: {} },
      { kind: "executor", plugin: "general_multi_turn", params: { goal: "", rounds: 3 } },
      { kind: "converter_method", plugin: "base64", params: { wrap: false } },
    ],
    scorers: [{ plugin: "refusal", params: {} }],
    sampling: { limit: 25, shuffle: true, seed: 42 },
    timeout_seconds: 120,
  });
  assert.equal("targets" in payload.template, false);
  assert.equal("dataset" in payload.template, false);
});

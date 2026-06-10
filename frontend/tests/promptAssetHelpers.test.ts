import assert from "node:assert/strict";
import test from "node:test";

import {
  changedLineRows,
  extractTemplateVariables,
  validateTemplateVariables,
} from "../src/lib/promptAssetHelpers.js";

test("extractTemplateVariables returns unique placeholders in first-seen order", () => {
  assert.deepEqual(
    extractTemplateVariables("Hello {goal}. Judge {goal} with {rubric}. Use {escaped}."),
    ["goal", "rubric", "escaped"],
  );
});

test("validateTemplateVariables reports missing and unused variables", () => {
  assert.deepEqual(
    validateTemplateVariables(["goal", "rubric", "unused"], "Attack {goal}"),
    {
      missing: [],
      unused: ["rubric", "unused"],
    },
  );
  assert.deepEqual(
    validateTemplateVariables(["goal"], "Attack {goal} with {rubric}"),
    {
      missing: ["rubric"],
      unused: [],
    },
  );
});

test("changedLineRows marks line-level differences by index", () => {
  assert.deepEqual(
    changedLineRows("a\nb\nc", "a\nB\nc\nnew"),
    [
      { lineNumber: 1, base: "a", draft: "a", changed: false },
      { lineNumber: 2, base: "b", draft: "B", changed: true },
      { lineNumber: 3, base: "c", draft: "c", changed: false },
      { lineNumber: 4, base: "", draft: "new", changed: true },
    ],
  );
});

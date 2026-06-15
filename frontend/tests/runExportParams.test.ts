import assert from "node:assert/strict";
import test from "node:test";

import { buildAttemptExportParams } from "../src/lib/runExport.js";

test("buildAttemptExportParams carries active attempt filters without pagination", () => {
  assert.deepEqual(
    buildAttemptExportParams("csv", {
      verdict: "complied",
      status: "completed",
      targetId: "target-1",
      executor: "single_turn",
    }),
    {
      format: "csv",
      verdict: "complied",
      status: "completed",
      target_id: "target-1",
      executor: "single_turn",
    },
  );
});

test("buildAttemptExportParams omits inactive filters", () => {
  assert.deepEqual(
    buildAttemptExportParams("json", {
      verdict: "",
      status: "",
      targetId: "",
      executor: "",
    }),
    { format: "json" },
  );
});

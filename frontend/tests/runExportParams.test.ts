import assert from "node:assert/strict";
import test from "node:test";

import {
  buildAttemptExportParams,
  buildHtmlReportExportParams,
  buildRunReportFilename,
} from "../src/lib/runExport.js";

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

test("buildHtmlReportExportParams carries the current language", () => {
  assert.deepEqual(buildHtmlReportExportParams("zh"), { lang: "zh" });
  assert.deepEqual(buildHtmlReportExportParams("en"), { lang: "en" });
});

test("buildRunReportFilename creates a safe html report filename", () => {
  assert.equal(
    buildRunReportFilename("My Run/Unsafe", "1234567890abcdef"),
    "My Run-Unsafe-12345678-report.html",
  );
  assert.equal(buildRunReportFilename("", "abcdef1234567890"), "run-abcdef12-report.html");
});

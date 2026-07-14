import assert from "node:assert/strict";
import test from "node:test";

import { buildRetestPath } from "../src/lib/retestSelection.js";

test("buildRetestPath preserves target and every selected source run", () => {
  const path = buildRetestPath("target/one", ["run-1", "run-2"]);
  const url = new URL(path, "https://airedteam.example");
  assert.equal(url.pathname, "/runs/retest");
  assert.equal(url.searchParams.get("target"), "target/one");
  assert.deepEqual(url.searchParams.getAll("run"), ["run-1", "run-2"]);
});

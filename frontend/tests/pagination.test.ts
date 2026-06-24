import assert from "node:assert/strict";
import test from "node:test";

import { buildPageWindow, formatPaginationRange } from "../src/lib/pagination.js";

test("buildPageWindow returns a compact one-based page window around current page", () => {
  assert.deepEqual(buildPageWindow({ page: 0, pageCount: 12 }), [1, 2, 3, 4, 5]);
  assert.deepEqual(buildPageWindow({ page: 5, pageCount: 12 }), [4, 5, 6, 7, 8]);
  assert.deepEqual(buildPageWindow({ page: 11, pageCount: 12 }), [8, 9, 10, 11, 12]);
});

test("formatPaginationRange describes the current slice", () => {
  assert.equal(formatPaginationRange({ total: 123, offset: 0, limit: 25 }), "1-25 of 123");
  assert.equal(formatPaginationRange({ total: 123, offset: 100, limit: 25 }), "101-123 of 123");
  assert.equal(formatPaginationRange({ total: 0, offset: 0, limit: 25 }), "0-0 of 0");
});

// SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
// SPDX-License-Identifier: MIT

import assert from "node:assert/strict";
import { test } from "node:test";

import { ALLOWED, advisories, review } from "../scripts/audit.mjs";

const SAMPLE = { "GHSA-ch52-4w7c-c8xp": "example reason" };

const report = {
  vulnerabilities: {
    "http-cache-semantics": {
      via: [{ url: "https://github.com/advisories/GHSA-ch52-4w7c-c8xp" }, "astro"],
    },
    astro: { via: ["http-cache-semantics"] },
  },
};

test("advisories reads every GHSA id and ignores package-name links", () => {
  assert.deepEqual([...advisories(report)], ["GHSA-ch52-4w7c-c8xp"]);
});

test("advisories is empty when there is nothing to report", () => {
  assert.equal(advisories({}).size, 0);
});

test("an advisory in the allowlist does not fail the build", () => {
  const { unexpected, unused } = review(advisories(report), SAMPLE);
  assert.deepEqual(unexpected, []);
  assert.deepEqual(unused, []);
});

test("an advisory outside the allowlist fails the build", () => {
  const found = new Set(["GHSA-ch52-4w7c-c8xp", "GHSA-0000-0000-0000"]);
  assert.deepEqual(review(found, SAMPLE).unexpected, ["GHSA-0000-0000-0000"]);
});

test("an allowlist entry no longer reported is flagged as unused", () => {
  assert.deepEqual(review(new Set(), SAMPLE).unused, Object.keys(SAMPLE));
});

test("the live allowlist is currently empty", () => {
  assert.deepEqual(Object.keys(ALLOWED), []);
});

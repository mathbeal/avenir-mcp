// SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
// SPDX-License-Identifier: MIT

// `npm audit` for the documentation site, with named exceptions.
//
// `npm audit` alone fails the build on every advisory in the whole build
// toolchain, including ones that have no fix and no bearing here: the site is
// static HTML with no runtime, so a server-side library's flaw cannot be
// reached. This runs the same audit but fails only on an advisory that is not
// in ALLOWED below. Each exception is dated and says why; remove it once a fix
// ships (an unseen exception is reported so the list stays honest).

import { execFileSync } from "node:child_process";

/**
 * Advisories reviewed and accepted, by GHSA id. Keep each one justified and
 * dated; delete it when the dependency can be upgraded past the advisory.
 * @type {Record<string, string>}
 */
export const ALLOWED = {
  // No advisories are accepted right now. Add one here as "GHSA-id": "dated reason"
  // only when it has no fix and cannot be reached by the static site.
};

/**
 * The GHSA ids of every advisory `npm audit --json` reports.
 * @param {{vulnerabilities?: Record<string, {via?: Array<string | {url?: string}>}>}} report
 * @returns {Set<string>}
 */
export function advisories(report) {
  const ids = new Set();
  for (const vuln of Object.values(report.vulnerabilities ?? {})) {
    for (const via of vuln.via ?? []) {
      if (typeof via === "object" && via.url) ids.add(via.url.split("/").pop());
    }
  }
  return ids;
}

/**
 * Advisories that must fail the build (reported, not allowed) and allowlist
 * entries no longer seen (safe to delete).
 * @param {Set<string>} found
 * @param {Record<string, string>} allowed
 */
export function review(found, allowed) {
  const unexpected = [...found].filter((id) => !(id in allowed));
  const unused = Object.keys(allowed).filter((id) => !found.has(id));
  return { unexpected, unused };
}

function main() {
  let json = "";
  try {
    json = execFileSync("npm", ["audit", "--json"], { encoding: "utf8" });
  } catch (error) {
    // `npm audit` exits non-zero when it finds advisories; the report is on stdout.
    json = error.stdout?.toString() ?? "";
    if (!json) throw error;
  }
  const { unexpected, unused } = review(advisories(JSON.parse(json)), ALLOWED);
  for (const id of unused) {
    console.log(`note: allowlisted ${id} is no longer reported; remove it from ALLOWED.`);
  }
  if (unexpected.length > 0) {
    console.error(`npm audit: advisories not in the allowlist:\n${unexpected.join("\n")}`);
    console.error("Fix them, or, if they cannot be reached here, add them to ALLOWED with a reason.");
    process.exit(1);
  }
  const count = Object.keys(ALLOWED).length;
  console.log(`npm audit: no advisory outside the allowlist (${count} accepted).`);
}

if (import.meta.url === `file://${process.argv[1]}`) main();

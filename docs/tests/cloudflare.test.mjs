// The site on Cloudflare Pages: the security headers it sends and the redirect to /avenir-mcp/.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { REQUIRED, checkHeaders, fillHeaders, headersForAllPaths, inlineHashes } from '../scripts/cloudflare.mjs';

const read = (/** @type {string} */ name) => readFileSync(new URL(`../cloudflare/${name}`, import.meta.url), 'utf8');
const template = read('_headers');
const hash = (/** @type {string} */ text) => `'sha256-${createHash('sha256').update(text).digest('base64')}'`;
const filled = fillHeaders(template, { scripts: new Set([hash('a()'), hash('b()')]), styles: new Set([hash('p{}')]) });

test('every path gets the four headers of a hardened site', () => {
  checkHeaders(filled);
  const headers = headersForAllPaths(filled);
  for (const name of REQUIRED) assert.ok(headers.has(name.toLowerCase()), name);
  assert.equal(headers.get('x-frame-options'), 'DENY');
  assert.equal(headers.get('x-content-type-options'), 'nosniff');
});

test('the policy names each inline script and style by its hash', () => {
  const csp = headersForAllPaths(filled).get('content-security-policy') ?? '';
  const scripts = [hash('a()'), hash('b()')].sort().join(' ');
  assert.ok(csp.includes(`script-src 'self' 'wasm-unsafe-eval' ${scripts};`));
  assert.ok(csp.includes(`style-src 'self' ${hash('p{}')};`));
});

test('dropping a required header, or weakening one, fails the check', () => {
  for (const name of REQUIRED) {
    const without = filled.split('\n').filter((line) => !line.trim().startsWith(`${name}:`)).join('\n');
    assert.throws(() => checkHeaders(without), new RegExp(name));
  }
  assert.throws(() => checkHeaders(filled.replace("frame-ancestors 'none'", "frame-ancestors *")), /frame-ancestors/);
  assert.throws(() => checkHeaders(filled.replace("script-src 'self'", "script-src 'self' 'unsafe-inline'")), /unsafe-inline/);
  assert.throws(() => checkHeaders(filled.replace('max-age=31536000', 'max-age=60')), /Strict-Transport-Security/);
  assert.throws(() => checkHeaders(filled.replace('X-Frame-Options: DENY', 'X-Frame-Options: ALLOWALL')), /X-Frame-Options/);
  assert.throws(() => checkHeaders(template), /placeholder/);
});

test('inline scripts and styles are hashed as written; external scripts are not', () => {
  const page = '<script type="module" src="/a.js"></script><script>x&amp;y</script><style>p{}</style>';
  const { scripts, styles } = inlineHashes(page);
  assert.deepEqual([...scripts], [hash('x&amp;y')]);
  assert.deepEqual([...styles], [hash('p{}')]);
});

test('the root redirects to the site, permanently', () => {
  const rules = read('_redirects')
    .split('\n')
    .filter((line) => line.trim() && !line.startsWith('#'))
    .map((line) => line.trim().split(/\s+/));
  assert.deepEqual(rules, [
    ['/', '/avenir-mcp/', '301'],
    ['/index.html', '/avenir-mcp/', '301'],
  ]);
});

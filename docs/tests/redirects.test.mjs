// SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
// SPDX-License-Identifier: MIT

// GitHub Pages only redirects: every old address leads to the same page on Cloudflare Pages.
import assert from 'node:assert/strict';
import { runInNewContext } from 'node:vm';
import { test } from 'node:test';
import { TARGET, notFoundPage, pagePath, redirects } from '../scripts/redirects.mjs';

const built = ['index.html', 'fr/index.html', 'guides/classify/index.html', '404.html'];

test('the site lives on Cloudflare Pages, under the same base', () => {
  assert.equal(TARGET, 'https://avenir-mcp.pages.dev/avenir-mcp/');
});

test('a built file maps to the address of its page', () => {
  assert.equal(pagePath('index.html'), '');
  assert.equal(pagePath('fr/index.html'), 'fr/');
  assert.equal(pagePath('guides/classify/index.html'), 'guides/classify/');
  assert.equal(pagePath('robots.html'), 'robots.html');
});

test('each page redirects to the same path on the site, with a canonical link and a plain link', () => {
  const pages = redirects(built);
  assert.deepEqual([...pages.keys()].sort(), [...built].sort());
  for (const [file, path] of [
    ['index.html', ''],
    ['fr/index.html', 'fr/'],
    ['guides/classify/index.html', 'guides/classify/'],
  ]) {
    const html = pages.get(file) ?? '';
    const url = TARGET + path;
    assert.ok(html.includes(`<meta http-equiv="refresh" content="0; url=${url}">`), file);
    assert.ok(html.includes(`<link rel="canonical" href="${url}">`), file);
    assert.ok(html.includes(`<a href="${url}">`), file);
  }
});

test('a page name is escaped in the markup', () => {
  const html = redirects(['a"b/index.html']).get('a"b/index.html') ?? '';
  assert.ok(!html.includes('a"b'));
  assert.ok(html.includes(`${TARGET}a%22b/`));
});

test('the 404 page sends any path under the base to the same path, and the rest home', () => {
  const html = notFoundPage();
  const script = /<script>([\s\S]*?)<\/script>/.exec(html)?.[1] ?? '';
  const visit = (/** @type {string} */ pathname, search = '', hash = '') => {
    let target = '';
    const location = { pathname, search, hash, replace: (/** @type {string} */ url) => (target = url) };
    runInNewContext(script, { location });
    return target;
  };
  assert.equal(visit('/avenir-mcp/old/page/', '?q=1', '#x'), `${TARGET}old/page/?q=1#x`);
  assert.equal(visit('/avenir-mcp/'), TARGET);
  assert.equal(visit('/elsewhere'), TARGET);
  assert.ok(html.includes(`<noscript><meta http-equiv="refresh" content="0; url=${TARGET}"></noscript>`));
  assert.ok(html.includes(`<a href="${TARGET}">`));
});

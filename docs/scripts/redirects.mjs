// SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
// SPDX-License-Identifier: MIT

// Builds what GitHub Pages publishes into redirect-dist/: no site, only redirects to the site
// on Cloudflare Pages, which sends the security headers GitHub Pages cannot. Each page of the
// built site (dist/) gets a page at the same path that sends the reader to the same address
// on Cloudflare; 404.html sends any other path there too, or to the home page.
import { mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

/** Where the site lives, base included, with a trailing slash. */
export const TARGET = 'https://avenir-mcp.pages.dev/avenir-mcp/';

/** The base GitHub Pages serves the repository's pages under. */
export const BASE = '/avenir-mcp/';

/** @param {string} text */
const escape = (text) =>
  text.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/**
 * The address of a built page on the site, from its file path relative to dist/:
 * `guides/classify/index.html` is `guides/classify/`, `index.html` the home page.
 * @param {string} file a path with forward slashes
 */
export function pagePath(file) {
  if (file === 'index.html') return '';
  if (file.endsWith('/index.html')) return file.slice(0, -'index.html'.length);
  return file;
}

/**
 * A page that sends the reader to `url` at once, and names it as the canonical address:
 * search engines take an immediate refresh as a permanent redirect.
 * @param {string} url
 */
export function redirectPage(url) {
  const href = escape(encodeURI(url));
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>avenir-mcp: moved</title>
<link rel="canonical" href="${href}">
<meta http-equiv="refresh" content="0; url=${href}">
</head>
<body>
<p>The documentation of avenir-mcp has moved: <a href="${href}">${href}</a>.</p>
</body>
</html>
`;
}

/**
 * The script of the 404 page: the same path on the site, or its home page when the path is
 * not under the base.
 */
export const NOT_FOUND_SCRIPT =
  `var p=location.pathname,b=${JSON.stringify(BASE)};` +
  `location.replace(p.indexOf(b)===0?${JSON.stringify(TARGET)}+p.slice(b.length)+location.search+location.hash:${JSON.stringify(TARGET)});`;

/**
 * The page GitHub Pages answers for a path it does not have: the same path on the site,
 * or its home page when the path is not under the base.
 */
export function notFoundPage() {
  const home = escape(TARGET);
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>avenir-mcp: moved</title>
<meta name="robots" content="noindex">
<script>${NOT_FOUND_SCRIPT}</script>
<noscript><meta http-equiv="refresh" content="0; url=${home}"></noscript>
</head>
<body>
<p>The documentation of avenir-mcp has moved: <a href="${home}">${home}</a>.</p>
</body>
</html>
`;
}

/** @param {string} dir */
function* htmlFiles(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(path);
    else if (entry.name.endsWith('.html')) yield path;
  }
}

/**
 * The redirect files for the pages of a built site, by path relative to the output.
 * @param {string[]} files paths of the built HTML pages relative to dist/, with forward slashes
 */
export function redirects(files) {
  /** @type {Map<string, string>} */
  const out = new Map();
  for (const file of files) {
    if (file === '404.html') continue;
    out.set(file, redirectPage(TARGET + pagePath(file)));
  }
  out.set('404.html', notFoundPage());
  return out;
}

function main() {
  const docs = fileURLToPath(new URL('..', import.meta.url));
  const dist = join(docs, 'dist');
  const out = join(docs, 'redirect-dist');
  rmSync(out, { recursive: true, force: true });
  const files = [...htmlFiles(dist)].map((file) => relative(dist, file).split(sep).join('/'));
  if (!files.includes('index.html')) throw new Error('dist/ has no index.html: run `npm run build` first');
  const pages = redirects(files);
  for (const [file, html] of pages) {
    const path = join(out, ...file.split('/'));
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, html);
  }
  console.log(`redirect-dist/ ready: ${pages.size} pages redirect to ${TARGET}`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();

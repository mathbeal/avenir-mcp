// Builds the site for Cloudflare Pages into cloudflare-dist/: the pages under /avenir-mcp/,
// as on GitHub Pages, with the _redirects and _headers files of cloudflare/ at the root.
// The Content-Security-Policy allows each inline <script> and <style> of the built pages by
// its hash, so the hashes are computed here, from the very files that are published.
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { copyFileSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const BASE = 'avenir-mcp';

/** The headers OpenSSF's `hardened_site` criterion asks for. */
export const REQUIRED = [
  'Content-Security-Policy',
  'Strict-Transport-Security',
  'X-Content-Type-Options',
  'X-Frame-Options',
];

/** Cloudflare ignores the rest of a longer line of _headers. */
const MAX_LINE = 2000;

/** @param {string} text */
const sha256 = (text) => `'sha256-${createHash('sha256').update(text, 'utf8').digest('base64')}'`;

/**
 * The CSP sources of the inline scripts and styles of one page. A browser hashes the text
 * between the tags exactly as written: no entity is decoded inside <script> or <style>.
 * @param {string} html
 */
export function inlineHashes(html) {
  const scripts = new Set();
  const styles = new Set();
  for (const [, body] of html.matchAll(/<script\b(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi)) {
    scripts.add(sha256(body));
  }
  for (const [, body] of html.matchAll(/<style\b[^>]*>([\s\S]*?)<\/style>/gi)) {
    styles.add(sha256(body));
  }
  return { scripts, styles };
}

/**
 * @param {string} template
 * @param {{ scripts: Set<string>, styles: Set<string> }} hashes
 */
export function fillHeaders(template, { scripts, styles }) {
  return template
    .replace('{{SCRIPT_HASHES}}', [...scripts].sort().join(' '))
    .replace('{{STYLE_HASHES}}', [...styles].sort().join(' '));
}

/**
 * The headers of the rule for every path, by lower-case name.
 * @param {string} text the content of a _headers file
 */
export function headersForAllPaths(text) {
  /** @type {Map<string, string>} */
  const headers = new Map();
  let inRule = false;
  for (const line of text.split('\n')) {
    if (line.trim() === '' || line.trimStart().startsWith('#')) continue;
    if (!/^\s/.test(line)) {
      inRule = line.trim() === '/*';
      continue;
    }
    if (!inRule) continue;
    const colon = line.indexOf(':');
    headers.set(line.slice(0, colon).trim().toLowerCase(), line.slice(colon + 1).trim());
  }
  return headers;
}

/**
 * Throws unless the file sends the required headers, with values that protect, to every path.
 * @param {string} text the content of a _headers file, placeholders filled
 */
export function checkHeaders(text) {
  const problems = [];
  if (text.includes('{{')) problems.push('a placeholder was left unfilled');
  for (const line of text.split('\n')) {
    if (line.length > MAX_LINE) problems.push(`a line is longer than ${MAX_LINE} characters`);
  }
  const headers = headersForAllPaths(text);
  for (const name of REQUIRED) {
    if (!headers.has(name.toLowerCase())) problems.push(`${name} is missing from the rule for /*`);
  }
  const csp = headers.get('content-security-policy') ?? '';
  /** @type {Map<string, string[]>} */
  const directives = new Map(
    csp
      .split(';')
      .map((part) => part.trim().split(/\s+/))
      .filter(([name]) => name)
      .map(([name, ...values]) => [name, values]),
  );
  /** @type {[string, string][]} */
  const expected = [
    ['default-src', "'self'"],
    ['object-src', "'none'"],
    ['base-uri', "'self'"],
    ['form-action', "'self'"],
    ['frame-ancestors', "'none'"],
  ];
  for (const [name, value] of expected) {
    if (directives.get(name)?.join(' ') !== value) problems.push(`the CSP needs ${name} ${value}`);
  }
  for (const [name, values] of directives) {
    if (values.includes('*') || values.some((v) => /^(https?|data|blob):?$/.test(v) && name !== 'img-src')) {
      problems.push(`the CSP lets ${name} load from anywhere`);
    }
    if (name !== 'style-src-attr' && values.includes("'unsafe-inline'")) {
      problems.push(`the CSP allows 'unsafe-inline' in ${name}`);
    }
    if (values.includes("'unsafe-eval'")) problems.push(`the CSP allows 'unsafe-eval' in ${name}`);
  }
  const maxAge = Number(/max-age=(\d+)/.exec(headers.get('strict-transport-security') ?? '')?.[1] ?? 0);
  if (maxAge < 31536000) problems.push('Strict-Transport-Security needs a max-age of a year or more');
  if (headers.has('x-content-type-options') && headers.get('x-content-type-options') !== 'nosniff') {
    problems.push('X-Content-Type-Options must be nosniff');
  }
  if (headers.has('x-frame-options') && !['DENY', 'SAMEORIGIN'].includes(headers.get('x-frame-options') ?? '')) {
    problems.push('X-Frame-Options must be DENY or SAMEORIGIN');
  }
  if (problems.length) throw new Error(`_headers: ${problems.join('; ')}`);
}

/** @param {string} dir */
function* htmlFiles(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(path);
    else if (entry.name.endsWith('.html')) yield path;
  }
}

function main() {
  const docs = fileURLToPath(new URL('..', import.meta.url));
  const out = join(docs, 'cloudflare-dist');
  const site = join(out, BASE);
  rmSync(out, { recursive: true, force: true });

  const astro = join(docs, 'node_modules', 'astro', 'bin', 'astro.mjs');
  const build = spawnSync(process.execPath, [astro, 'build', '--outDir', site], { cwd: docs, stdio: 'inherit' });
  if (build.status !== 0) process.exit(build.status ?? 1);

  const hashes = { scripts: new Set(), styles: new Set() };
  for (const file of htmlFiles(site)) {
    const page = inlineHashes(readFileSync(file, 'utf8'));
    page.scripts.forEach((h) => hashes.scripts.add(h));
    page.styles.forEach((h) => hashes.styles.add(h));
  }
  const headers = fillHeaders(readFileSync(join(docs, 'cloudflare', '_headers'), 'utf8'), hashes);
  writeFileSync(join(out, '_headers'), headers);
  copyFileSync(join(docs, 'cloudflare', '_redirects'), join(out, '_redirects'));
  // Without a 404.html at the root, Cloudflare Pages would answer every unknown path with
  // the root page, as for a single-page application.
  copyFileSync(join(site, '404.html'), join(out, '404.html'));

  checkHeaders(readFileSync(join(out, '_headers'), 'utf8'));
  console.log(
    `cloudflare-dist/ ready: ${hashes.scripts.size} inline scripts and ${hashes.styles.size} inline styles allowed by hash`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main();

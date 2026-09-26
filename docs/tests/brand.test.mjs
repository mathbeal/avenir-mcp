// The name avenir-mcp is set apart in the text of a page, never in code or in a path.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { markdownToHtml } from 'satteri';
import { branded } from '../src/components/home-i18n.ts';
import { brand } from '../src/plugins/brand.mjs';

const SPAN = '<span class="brand">avenir-mcp</span>';

/** @param {string} source */
const render = (source) => markdownToHtml(source, { hastPlugins: [brand] }).html;

test('a mention in the text is set apart, every time', () => {
  assert.equal(render('Run avenir-mcp, then avenir-mcp again.'), `<p>Run ${SPAN}, then ${SPAN} again.</p>\n`);
});

test('a mention in a heading, a link or emphasis is set apart too', () => {
  const html = render('## Add avenir-mcp\n\n[avenir-mcp](/avenir-mcp/x/) and *avenir-mcp*');
  assert.equal(html.split(SPAN).length - 1, 3);
  assert.match(html, /href="\/avenir-mcp\/x\/"/);
});

test('code, inline or in a block, stays as written', () => {
  const html = render('`uvx avenir-mcp`\n\n```sh\nclaude mcp add avenir-mcp\n```');
  assert.doesNotMatch(html, /class="brand"/);
  assert.match(html, /uvx avenir-mcp/);
  assert.match(html, /claude mcp add avenir-mcp/);
});

test('text without the name is left untouched', () => {
  assert.equal(render('An MCP server for YNAB.'), '<p>An MCP server for YNAB.</p>\n');
});

test('the home page sets the name apart but leaves paths and longer words alone', () => {
  assert.equal(branded('avenir-mcp computes it.'), `${SPAN} computes it.`);
  assert.equal(
    branded('<a href="/avenir-mcp/fr/project/legal/">avenir-mcp</a>'),
    `<a href="/avenir-mcp/fr/project/legal/">${SPAN}</a>`,
  );
  assert.equal(branded('avenir-mcp-bundle and my-avenir-mcp'), 'avenir-mcp-bundle and my-avenir-mcp');
});

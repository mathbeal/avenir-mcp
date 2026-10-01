// SPDX-FileCopyrightText: 2026 The avenir-mcp contributors
// SPDX-License-Identifier: MIT

// Sets the name "avenir-mcp" apart from the prose around it: every mention in the
// text of a page becomes <span class="brand">avenir-mcp</span>, styled in theme.css.
// Code stays as written: a command or a config file is copied, not read.
import { defineHastPlugin } from 'satteri';

const NAME = 'avenir-mcp';
const LEAVE_ALONE = new Set(['code', 'pre', 'script', 'style', 'kbd', 'samp']);

/** @param {string} text */
function split(text) {
  /** @type {any[]} */
  const nodes = [];
  text.split(NAME).forEach((part, index) => {
    if (index > 0) {
      nodes.push({
        type: 'element',
        tagName: 'span',
        properties: { className: ['brand'] },
        children: [{ type: 'text', value: NAME }],
      });
    }
    if (part) nodes.push({ type: 'text', value: part });
  });
  return nodes;
}

/** @param {any} node @param {any} ctx */
function inCode(node, ctx) {
  for (let up = ctx.parent(node); up; up = ctx.parent(up)) {
    if (up.type === 'element' && LEAVE_ALONE.has(up.tagName)) return true;
  }
  return false;
}

export const brand = defineHastPlugin({
  name: 'avenir-brand',
  text(node, ctx) {
    if (node.value.includes(NAME) && !inCode(node, ctx)) ctx.replaceNode(node, split(node.value));
  },
});

// Markdown tables: a scroll box around each, and sensible break points in the
// long identifiers their cells hold.
//
// A table spans the content column, and one with more columns than the
// column has room for must pan rather than run under the contents list. A
// table element cannot do both: made a scrolling block (Starlight's default)
// it shrinks to its content, and made a full-width table it cannot scroll. So
// the table fills the column and a `<div class="ds-table">` wrapper does the
// scrolling; see "Tables" in foundation.css.
//
// Cells hold identifiers, paths and digests that have no spaces. Left alone
// they either force their column wide or, allowed to break anywhere, crumble
// a character at a time. Instead each long token gets a `<wbr>` after its own
// separators — `_ - / . :` — and a long hex digest splits into even pieces of
// at most sixteen characters, so it wraps where a reader would split it.
//
// Kept identical in the UsageBench repository.

/** Tokens shorter than this never need a break. */
const LONG = 14;
const SEPARATOR = /[_\-/.:]/;
const HEX_RUN = /^[0-9a-f]{16,}$/i;

/** Splits one long token into pieces, each ending where a break belongs. */
function pieces(token) {
  if (HEX_RUN.test(token)) {
    // Even pieces of at most sixteen: a 40-character revision in three, a
    // 64-character digest in four.
    const size = Math.ceil(token.length / Math.ceil(token.length / 16));
    return token.match(new RegExp(`.{1,${size}}`, 'g'));
  }
  const out = [];
  let start = 0;
  for (let i = 0; i < token.length - 1; i++) {
    if (SEPARATOR.test(token[i])) {
      out.push(token.slice(start, i + 1));
      start = i + 1;
    }
  }
  out.push(token.slice(start));
  return out;
}

/** Text node → text and `<wbr>` nodes, or null when nothing is long. */
function breakText(value) {
  const parts = value.split(/(\s+)/);
  if (!parts.some((part) => part.length >= LONG && !/\s/.test(part))) return null;
  const nodes = [];
  let pending = '';
  for (const part of parts) {
    if (part.length < LONG || /\s/.test(part)) {
      pending += part;
      continue;
    }
    const split = pieces(part);
    split.forEach((piece, index) => {
      pending += piece;
      if (index < split.length - 1) {
        nodes.push({ type: 'text', value: pending });
        nodes.push({ type: 'element', tagName: 'wbr', properties: {}, children: [] });
        pending = '';
      }
    });
  }
  if (pending) nodes.push({ type: 'text', value: pending });
  return nodes;
}

/** @param {any} node */
function addBreaks(node) {
  if (!Array.isArray(node.children)) return;
  node.children = node.children.flatMap((child) => {
    if (child.type === 'text') return breakText(child.value) ?? [child];
    addBreaks(child);
    return [child];
  });
}

/** @param {any} node */
function wrapTables(node) {
  if (!Array.isArray(node.children)) return;
  node.children = node.children.map((child) => {
    if (child.type === 'element' && child.tagName === 'table') {
      addBreaks(child);
      return {
        type: 'element',
        tagName: 'div',
        properties: { className: ['ds-table'] },
        children: [child],
      };
    }
    wrapTables(child);
    return child;
  });
}

export function rehypeTableScroll() {
  return (/** @type {any} */ tree) => wrapTables(tree);
}

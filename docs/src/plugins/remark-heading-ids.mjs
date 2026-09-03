// Explicit heading anchors for markdown/MDX content: `## Heading {#custom-id}`.
//
// Snapshot pages lifted their section headings out of Astro components and
// into MDX so Starlight's "On this page" nav can see them, but the anchor ids
// those components published are citable and must not move. The auto-slugger
// would derive a different id from the heading text, so each lifted heading
// declares the legacy id explicitly and this plugin honours it: the trailing
// `{#id}` marker is stripped from the visible text and set as the heading's
// id, which rehype-slug then leaves alone and Starlight's ToC picks up.
import { visit } from 'unist-util-visit';

const MARKER = /\s*\{#([A-Za-z][\w-]*)\}\s*$/;

export function remarkHeadingIds() {
  return (tree) => {
    visit(tree, 'heading', (node) => {
      const last = node.children.at(-1);
      if (!last || last.type !== 'text') return;
      const match = last.value.match(MARKER);
      if (!match) return;
      last.value = last.value.slice(0, match.index).replace(/\s+$/, '');
      if (last.value === '') node.children.pop();
      node.data ??= {};
      node.data.hProperties = { ...node.data.hProperties, id: match[1] };
    });
  };
}

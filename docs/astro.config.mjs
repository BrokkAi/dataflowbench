// @ts-check
import { readdirSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { snapshots } from './src/data/snapshots';

// ---------------------------------------------------------------------------
// Snapshot navigation.
//
// The sidebar carries exactly three snapshot entries — the current freeze
// (expanded), the one it superseded (collapsed), and a single link to the
// archive page that lists everything older. Every archived snapshot keeps its
// URL: this is navigation, not unpublication, and the freeze contract's
// citability depends on those URLs never moving.
//
// All three entries are derived from `src/data/snapshots.ts`, which is
// newest-first, so cutting the next release needs no edit here.
// ---------------------------------------------------------------------------

/** Sub-pages of a snapshot, in reading order. Not every freeze has them all. */
const snapshotPages = [
  ['index', 'Snapshot overview'],
  ['analyzers', 'Analyzers'],
  ['languages', 'Languages'],
  ['templates', 'Semantic templates'],
  ['evidence', 'Case evidence'],
  ['latency', 'Latency'],
  ['profiles', 'Analyzer profiles'],
];

/** The sub-page entries a snapshot actually has, read from its content dir. */
function snapshotItems(snapshot) {
  const dir = new URL(
    `./src/content/docs/snapshots/${snapshot.slug}/`,
    import.meta.url,
  );
  const present = new Set(
    readdirSync(dir).map((file) => file.replace(/\.mdx?$/, '')),
  );
  return snapshotPages
    .filter(([name]) => present.has(name))
    .map(([name, label]) => ({
      label,
      slug:
        name === 'index'
          ? `snapshots/${snapshot.slug}`
          : `snapshots/${snapshot.slug}/${name}`,
    }));
}

const currentSnapshot = snapshots.find((snapshot) => snapshot.current);
if (!currentSnapshot) throw new Error('no current snapshot in the registry');
const previousSnapshot = snapshots[snapshots.indexOf(currentSnapshot) + 1];
const currentLabel = `${currentSnapshot.version} (current)`;
const previousLabel = previousSnapshot
  ? `${previousSnapshot.version} (previous)`
  : '';

// Production deployment target for GitHub Pages.
export default defineConfig({
  site: 'https://dataflowbench.brokk.ai',
  redirects: {
    // Explicit current-snapshot pointer alongside versioned snapshot URLs.
    '/current': `/snapshots/${currentSnapshot.slug}/`,
  },
  integrations: [
    starlight({
      title: 'DataFlowBench',
      favicon: '/favicon.svg',
      description:
        'Analyzer-neutral benchmark for data-flow analysis, published exclusively from immutable freeze evidence.',
      customCss: ['./src/styles/custom.css'],
      components: {
        // Starlight's own footer, with the floating "back to top" control
        // appended. The footer is the one slot that renders exactly once on
        // every page, including the landing page.
        Footer: './src/components/Footer.astro',
      },
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/BrokkAi/dataflowbench',
        },
      ],
      sidebar: [
        { label: 'Overview', slug: 'index' },
        { label: 'Methodology', slug: 'methodology' },
        { label: 'Scoring', slug: 'scoring' },
        { label: 'Reproduction', slug: 'reproduction' },
        {
          label: 'Snapshots',
          items: [
            {
              label: currentLabel,
              items: snapshotItems(currentSnapshot),
            },
            ...(previousSnapshot
              ? [
                  {
                    label: previousLabel,
                    collapsed: true,
                    items: snapshotItems(previousSnapshot),
                  },
                ]
              : []),
            { label: 'Older snapshots', slug: 'snapshots' },
          ],
        },
        {
          label: 'Contracts (repository)',
          items: [
            {
              label: 'Freeze contract',
              link: 'https://github.com/BrokkAi/dataflowbench/blob/main/docs/freeze.md',
            },
            {
              label: 'Result generation',
              link: 'https://github.com/BrokkAi/dataflowbench/blob/main/docs/results.md',
            },
            {
              label: 'Scoring contract',
              link: 'https://github.com/BrokkAi/dataflowbench/blob/main/docs/scoring.md',
            },
            {
              label: 'Adapter contract',
              link: 'https://github.com/BrokkAi/dataflowbench/blob/main/docs/adapters.md',
            },
            {
              label: 'Latency tier (preregistration)',
              link: 'https://github.com/BrokkAi/dataflowbench/blob/main/docs/latency-tier.md',
            },
          ],
        },
      ],
    }),
  ],
});

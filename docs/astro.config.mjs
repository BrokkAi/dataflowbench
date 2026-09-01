// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// Production deployment target for GitHub Pages.
export default defineConfig({
  site: 'https://brokkai.github.io',
  base: '/dataflowbench',
  redirects: {
    // Explicit current-snapshot pointer alongside versioned snapshot URLs.
    '/current': '/dataflowbench/snapshots/v0-6-0/',
  },
  integrations: [
    starlight({
      title: 'DataFlowBench',
      favicon: '/favicon.svg',
      description:
        'Analyzer-neutral benchmark for data-flow analysis, published exclusively from immutable freeze evidence.',
      customCss: ['./src/styles/custom.css'],
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
            { label: 'All snapshots', slug: 'snapshots' },
            {
              label: 'v0.6.0 (current)',
              items: [
                { label: 'Snapshot overview', slug: 'snapshots/v0-6-0' },
                { label: 'Analyzers', slug: 'snapshots/v0-6-0/analyzers' },
                { label: 'Languages', slug: 'snapshots/v0-6-0/languages' },
                { label: 'Semantic templates', slug: 'snapshots/v0-6-0/templates' },
                { label: 'Case evidence', slug: 'snapshots/v0-6-0/evidence' },
                { label: 'Latency', slug: 'snapshots/v0-6-0/latency' },
              ],
            },
            {
              label: 'v0.5.0 (archived)',
              collapsed: true,
              items: [
                { label: 'Snapshot overview', slug: 'snapshots/v0-5-0' },
                { label: 'Analyzers', slug: 'snapshots/v0-5-0/analyzers' },
                { label: 'Languages', slug: 'snapshots/v0-5-0/languages' },
                { label: 'Semantic templates', slug: 'snapshots/v0-5-0/templates' },
                { label: 'Case evidence', slug: 'snapshots/v0-5-0/evidence' },
              ],
            },
            {
              label: 'v0.4.0 (archived)',
              collapsed: true,
              items: [
                { label: 'Snapshot overview', slug: 'snapshots/v0-4-0' },
                { label: 'Analyzers', slug: 'snapshots/v0-4-0/analyzers' },
                { label: 'Languages', slug: 'snapshots/v0-4-0/languages' },
                { label: 'Semantic templates', slug: 'snapshots/v0-4-0/templates' },
                { label: 'Case evidence', slug: 'snapshots/v0-4-0/evidence' },
              ],
            },
            {
              label: 'v0.3.0 (archived)',
              collapsed: true,
              items: [
                { label: 'Snapshot overview', slug: 'snapshots/v0-3-0' },
                { label: 'Analyzers', slug: 'snapshots/v0-3-0/analyzers' },
                { label: 'Languages', slug: 'snapshots/v0-3-0/languages' },
                { label: 'Semantic templates', slug: 'snapshots/v0-3-0/templates' },
                { label: 'Case evidence', slug: 'snapshots/v0-3-0/evidence' },
              ],
            },
            {
              label: 'v0.2.0 (archived)',
              collapsed: true,
              items: [
                { label: 'Snapshot overview', slug: 'snapshots/v0-2-0' },
                { label: 'Analyzers', slug: 'snapshots/v0-2-0/analyzers' },
                { label: 'Languages', slug: 'snapshots/v0-2-0/languages' },
                { label: 'Semantic templates', slug: 'snapshots/v0-2-0/templates' },
                { label: 'Case evidence', slug: 'snapshots/v0-2-0/evidence' },
              ],
            },
            {
              label: 'v0.1.0 (archived)',
              collapsed: true,
              items: [
                { label: 'Snapshot overview', slug: 'snapshots/v0-1-0' },
                { label: 'Analyzers', slug: 'snapshots/v0-1-0/analyzers' },
                { label: 'Languages', slug: 'snapshots/v0-1-0/languages' },
                { label: 'Semantic templates', slug: 'snapshots/v0-1-0/templates' },
                { label: 'Case evidence', slug: 'snapshots/v0-1-0/evidence' },
              ],
            },
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

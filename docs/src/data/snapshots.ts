// The single source of numerical truth for the site. Every count, rate, and
// digest rendered on a page comes from a generated results model produced by
// `cargo run -- generate-results` from a validated immutable freeze — never
// from hand-authored prose. CI proves the checked-in model is current.
import currentResults from '../../../results/results.json';
import v061Results from './archive/v0-6-1-results.json';
import v060Results from './archive/v0-6-0-results.json';
import v050Results from './archive/v0-5-0-results.json';
import v040Results from './archive/v0-4-0-results.json';
import v030Results from './archive/v0-3-0-results.json';
import v020Results from './archive/v0-2-0-results.json';
import v010Results from './archive/v0-1-0-results.json';
import { latencyEvidenceRelease } from './latency-sources';

export interface RateFraction {
  numerator: number;
  denominator: number;
  percent: string;
}

export interface TemplateMacro {
  true_positive_rate_percent: string | null;
  false_positive_rate_percent: string | null;
  scored_positive_templates: number;
  scored_negative_templates: number;
}

export interface DimensionCounts {
  true_positives: number;
  false_negatives: number;
  false_positives: number;
  true_negatives: number;
  inconclusive: number;
  unsupported: number;
  runner_errors: number;
}

export interface SemanticDimension {
  name: string;
  counts: DimensionCounts;
  true_positive_rate: RateFraction | null;
  false_positive_rate: RateFraction | null;
  template_macro: TemplateMacro;
}

export interface CaseResult {
  case_id: string;
  template_id: string;
  polarity: string;
  semantic_dimensions: string[];
  outcome: string;
  classification: string;
  raw_evidence: { path: string; sha256: string };
}

export interface ScoreTier {
  score_tier: string;
  scored: boolean;
  outcome_coverage: Record<string, number>;
  semantic_dimensions: SemanticDimension[];
  dimension_macro: {
    true_positive_rate_percent: string | null;
    false_positive_rate_percent: string | null;
  };
  cases: CaseResult[];
}

export interface ScorecardLanguage {
  language: string;
  score_tiers: ScoreTier[];
}

export interface Adapter {
  id: string;
  tool: string;
  tool_version: string;
  build_identity: string;
  adapter_version: string;
  configuration_hash: string;
  track: string;
  dimension: string;
  model_profile: string;
}

export interface Scorecard {
  id: string;
  adapter: Adapter;
  track: string;
  dimension: string;
  model_profile: string;
  report: {
    path: string;
    sha256: string;
    normalized_report_sha256: string;
  };
  languages: ScorecardLanguage[];
}

export interface ResultsModel {
  schema_version: number;
  manifest: { path: string; sha256: string };
  benchmark: {
    revision: string;
    release: string;
    case_schema_version: number;
    result_schema_version: number;
    fixture_revision: string;
    dirty: boolean;
  };
  claim: {
    scope: string;
    tracks: string[];
    dimensions: string[];
    exclusions: { id: string; reason: string }[];
    score_tiers: string[];
    model_profiles: string[];
  };
  scorecards: Scorecard[];
}

export interface Snapshot {
  /** Release name of the freeze, e.g. `v0.1.0`. */
  version: string;
  /** URL-safe slug segment for this snapshot's pages. */
  slug: string;
  /** Git ref whose tree contains the manifest and retained evidence. */
  evidenceRef: string;
  /** Release whose immutable latency corpus this snapshot renders. */
  latencyEvidenceRelease?: string;
  current: boolean;
  results: ResultsModel;
}

export const repository = 'https://github.com/BrokkAi/dataflowbench';

export const snapshots: Snapshot[] = [
  {
    version: 'v0.7.0',
    slug: 'v0-7-0',
    evidenceRef: 'main',
    // v0.7.0 re-ran correctness only. It reuses the v0.6.0 latency corpus for
    // the same reason v0.6.1 did: nothing was re-measured, so nothing may be
    // relabelled onto the newer pins.
    latencyEvidenceRelease: latencyEvidenceRelease('v0.7.0'),
    current: true,
    results: currentResults as unknown as ResultsModel,
  },
  {
    version: 'v0.6.1',
    slug: 'v0-6-1',
    // Permanently pinned: the commit whose tree holds v0.6.1's manifest and
    // retained evidence, immutable even as main moves on. The A30 and A31
    // amendments landed on `main` after this commit and are deliberately not
    // in this archive: v0.6.1 published these outcomes, and this is what it
    // published.
    evidenceRef: '3eab449bcd40e037eee1b33e81a60cc646a600af',
    latencyEvidenceRelease: latencyEvidenceRelease('v0.6.1'),
    current: false,
    results: v061Results as unknown as ResultsModel,
  },
  {
    version: 'v0.6.0',
    slug: 'v0-6-0',
    // Permanently pinned: the commit whose tree holds v0.6.0's manifest and
    // retained evidence, immutable even as main moves on. Note that the
    // amendment rows added to `main` after this commit (A13/A14, A22/A23)
    // are deliberately *not* in this archive: v0.6.0 published 74 scorecards
    // and this is what it published.
    evidenceRef: 'c0c42013a35a19107b65e652f55952669c4b9ffe',
    latencyEvidenceRelease: latencyEvidenceRelease('v0.6.0'),
    current: false,
    results: v060Results as unknown as ResultsModel,
  },
  {
    version: 'v0.5.0',
    slug: 'v0-5-0',
    // Permanently pinned: the commit whose tree holds v0.5.0's manifest and
    // retained evidence, immutable even as main moves on.
    evidenceRef: 'd6582d1c29c121d4d3655874a7bab122444424b2',
    current: false,
    results: v050Results as unknown as ResultsModel,
  },
  {
    version: 'v0.4.0',
    slug: 'v0-4-0',
    // Permanently pinned: the commit whose tree holds v0.4.0's manifest and
    // retained evidence, immutable even as main moves on.
    evidenceRef: '86a29e0516f7701140769c9069e6d4dceede9e24',
    current: false,
    results: v040Results as unknown as ResultsModel,
  },
  {
    version: 'v0.3.0',
    slug: 'v0-3-0',
    // Permanently pinned: the commit whose tree holds v0.3.0's manifest and
    // retained evidence, immutable even as main moves on.
    evidenceRef: 'cd572c402c3d0c39a58db991428df87fca360c94',
    current: false,
    results: v030Results as unknown as ResultsModel,
  },
  {
    version: 'v0.2.0',
    slug: 'v0-2-0',
    // Permanently pinned: the commit whose tree holds v0.2.0's manifest and
    // retained evidence, immutable even as main moves on.
    evidenceRef: '16d001475f65f043f77d4701c6f4821d926f390c',
    current: false,
    results: v020Results as unknown as ResultsModel,
  },
  {
    version: 'v0.1.0',
    slug: 'v0-1-0',
    // Permanently pinned: the commit whose tree holds v0.1.0's manifest and
    // retained evidence, immutable even as main moves on.
    evidenceRef: 'd8dda057ea9d0c126480709d1a91df29e298433a',
    current: false,
    results: v010Results as unknown as ResultsModel,
  },
];

export const currentSnapshot: Snapshot = snapshots.find(
  (snapshot) => snapshot.current,
)!;

export function snapshotByVersion(version: string): Snapshot {
  const snapshot = snapshots.find((candidate) => candidate.version === version);
  if (!snapshot) throw new Error(`unknown snapshot ${version}`);
  return snapshot;
}

/** The shape of one snapshot at a glance, counted from its own results model. */
export interface SnapshotScale {
  /** Distinct analyzers bound in the freeze. */
  analyzers: number;
  /** Bound, digest-pinned normalized reports (scorecards). */
  reports: number;
  /** Distinct frozen case identifiers the freeze scored against. */
  cases: number;
}

/**
 * Counted at build time from the archived `results.json` of the freeze itself.
 * Nothing here is hand-entered: an archive index that restated its numbers in
 * prose would be exactly the kind of drift the freeze contract forbids.
 */
export function snapshotScale(results: ResultsModel): SnapshotScale {
  const analyzers = new Set<string>();
  const cases = new Set<string>();
  for (const card of results.scorecards) {
    analyzers.add(card.adapter.tool);
    for (const language of card.languages) {
      for (const tier of language.score_tiers) {
        for (const result of tier.cases) cases.add(result.case_id);
      }
    }
  }
  return {
    analyzers: analyzers.size,
    reports: results.scorecards.length,
    cases: cases.size,
  };
}

/** Link into the repository tree that holds this snapshot's frozen evidence. */
export function evidenceUrl(snapshot: Snapshot, path: string): string {
  return `${repository}/blob/${snapshot.evidenceRef}/${path}`;
}

export function shortDigest(sha256: string): string {
  return sha256.slice(0, 12);
}

export function percentCell(percent: string | null): string {
  return percent === null ? 'n/a' : `${percent}%`;
}

/** Display name for an analyzer, keyed by the adapter's tool identifier. */
const vendorNames: Record<string, string> = {
  bifrost: 'Bifrost',
  codeql: 'CodeQL',
  joern: 'Joern',
  semgrep: 'Semgrep CE',
  opentaint: 'OpenTaint',
  infer: 'Infer',
  flowdroid: 'FlowDroid',
  pysa: 'Pysa',
};

/**
 * Fixed vendor→colour identity map. Keyed by tool rather than by row position
 * so a vendor keeps its colour across every section and every snapshot.
 *
 * The first four slots are frozen: `v0`–`v3` were published in v0.1.0–v0.5.0
 * and a reader who learned "orange is CodeQL" from an archived snapshot must
 * still read it that way here. The four analyzers added in v0.6.0 therefore
 * take **new** slots `v4`–`v7` rather than reusing or reshuffling any of the
 * existing ones. Every consumer of this map defines all eight classes.
 */
const vendorColorClasses: Record<string, string> = {
  bifrost: 'v0',
  codeql: 'v1',
  joern: 'v2',
  semgrep: 'v3',
  opentaint: 'v4',
  infer: 'v5',
  flowdroid: 'v6',
  pysa: 'v7',
};

/** How many stable colour slots the stylesheets define. */
export const vendorColorSlots = 8;

export function vendorName(tool: string): string {
  return vendorNames[tool] ?? tool.charAt(0).toUpperCase() + tool.slice(1);
}

/**
 * The witnessed `tool_version` as a version *label*, for display beside the
 * analyzer's name. Bifrost's version banner witnesses itself as
 * `bifrost 0.10.9`, so rendering it next to the name reads "Bifrost bifrost
 * 0.10.9". The witnessed string in the manifest is untouched; only the label
 * drops the redundant prefix.
 */
export function toolVersionLabel(tool: string, toolVersion: string): string {
  const prefix = `${tool} `;
  return toolVersion.startsWith(prefix)
    ? toolVersion.slice(prefix.length)
    : toolVersion;
}

export function vendorColorClass(tool: string, index = 0): string {
  return vendorColorClasses[tool] ?? `v${index % vendorColorSlots}`;
}

/**
 * The identity map itself, for the one consumer that needs it as data: the
 * landing page's client-side dialog script, which cannot import this module
 * and would otherwise hand-copy the map and drift from it.
 */
export const vendorColorMap: Readonly<Record<string, string>> =
  vendorColorClasses;

/** Stable ordering of analyzers: the colour identity map, then alphabetical. */
export function vendorOrder(tool: string): number {
  const index = Object.keys(vendorColorClasses).indexOf(tool);
  return index === -1 ? Object.keys(vendorColorClasses).length : index;
}

/**
 * Comparison cohort for overview-level cross-analyzer figures.
 *
 * Generalists publish benchmark-controlled kernels across several language
 * ecosystems; specialists deliberately concentrate on one ecosystem or a
 * small related family. The distinction is presentation metadata, not a
 * score, and keeps unlike product scopes out of the same aggregate panel.
 */
export type AnalyzerCohort = 'generalist' | 'specialist';

const analyzerCohorts: Readonly<Record<string, AnalyzerCohort>> = {
  bifrost: 'generalist',
  codeql: 'generalist',
  joern: 'generalist',
  semgrep: 'generalist',
  opentaint: 'specialist',
  infer: 'specialist',
  flowdroid: 'specialist',
  pysa: 'specialist',
};

export function analyzerCohort(tool: string): AnalyzerCohort {
  // Unknown future adapters remain visible, but do not silently acquire the
  // narrower specialist label without an explicit classification decision.
  return analyzerCohorts[tool] ?? 'generalist';
}

/**
 * One benchmark-controlled `core` population, carrying every analyzer whose
 * own core tier covers exactly the same case identifiers.
 */
export interface CorePopulation {
  language: string;
  /** Assertions in the population. */
  cases: number;
  /** Distinct semantic templates behind those assertions. */
  templates: number;
  /** The tier that defined the population, used for its case list. */
  tier: ScoreTier;
  /** Analyzers covering this exact case set, keyed by tool identifier. */
  entries: Map<string, { card: Scorecard; tier: ScoreTier }>;
}

/**
 * The benchmark-controlled kernel populations of one snapshot — the no-pooling
 * filter the landing page reads, factored out so that the per-snapshot view and
 * the cross-snapshot view can never drift apart.
 *
 * Populations are matched by case identity, never by language name, so a
 * 15-template core and a 16-template core of the same language stay separate.
 * A scorecard covering many languages is a breadth run and may only *join* a
 * population that a dedicated single-language card already defined; the
 * breadth baseline's two-case cores never become kernels of their own.
 *
 * Non-core tiers are excluded explicitly at every schema version:
 * `calibration` (unscored), `language-extension` (v0.3.0+) and `modeling`
 * (v0.5.0+) never enter, and neither does any `tool-native` scorecard.
 */
export function coreKernelPopulations(results: ResultsModel): CorePopulation[] {
  const cards = results.scorecards.filter(
    (card) =>
      (card.model_profile ?? card.adapter.model_profile) ===
      'benchmark-controlled',
  );
  const isBreadth = (card: Scorecard) => card.languages.length > 1;
  const caseKey = (tier: ScoreTier) =>
    tier.cases
      .map((result) => result.case_id)
      .sort()
      .join('\n');

  const byPopulation = new Map<string, CorePopulation>();
  // Pass one: dedicated single-language cards define which populations are
  // kernels at all.
  for (const card of cards) {
    if (isBreadth(card)) continue;
    for (const language of card.languages) {
      for (const tier of language.score_tiers) {
        if (tier.score_tier !== 'core') continue;
        const key = caseKey(tier);
        if (byPopulation.has(key)) continue;
        byPopulation.set(key, {
          language: language.language,
          cases: tier.cases.length,
          templates: new Set(tier.cases.map((result) => result.template_id))
            .size,
          tier,
          entries: new Map(),
        });
      }
    }
  }
  // Pass two: every core tier — dedicated or breadth — joins the population it
  // covers exactly. A dedicated card always wins over a breadth card for the
  // same analyzer and the same cases.
  for (const card of cards) {
    for (const language of card.languages) {
      for (const tier of language.score_tiers) {
        if (tier.score_tier !== 'core') continue;
        const population = byPopulation.get(caseKey(tier));
        if (!population) continue;
        if (population.entries.has(card.adapter.tool) && isBreadth(card)) {
          continue;
        }
        population.entries.set(card.adapter.tool, { card, tier });
      }
    }
  }
  return [...byPopulation.values()]
    .filter((population) => population.entries.size > 0)
    .sort((left, right) => left.language.localeCompare(right.language));
}

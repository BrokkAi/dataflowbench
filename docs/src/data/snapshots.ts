// The single source of numerical truth for the site. Every count, rate, and
// digest rendered on a page comes from a generated results model produced by
// `cargo run -- generate-results` from a validated immutable freeze — never
// from hand-authored prose. CI proves the checked-in model is current.
import currentResults from '../../../results/results.json';
import v010Results from './archive/v0-1-0-results.json';

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
  current: boolean;
  results: ResultsModel;
}

export const repository = 'https://github.com/BrokkAi/dataflowbench';

export const snapshots: Snapshot[] = [
  {
    version: 'v0.2.0',
    slug: 'v0-2-0',
    evidenceRef: 'main',
    current: true,
    results: currentResults as unknown as ResultsModel,
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

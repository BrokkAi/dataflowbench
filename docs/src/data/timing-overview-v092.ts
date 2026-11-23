import publication from '../../../reports/timing/v0.9.2/publication-20261123-01/summary.json' with { type: 'json' };
import caseRows from '../../../reports/timing/v0.9.2/publication-20261123-01/cases.json' with { type: 'json' };

export type TimingOverviewAnalyzerId =
  | 'bifrost'
  | 'codeql'
  | 'joern'
  | 'semgrep'
  | 'opentaint'
  | 'infer'
  | 'flowdroid'
  | 'pysa';
export type TimingOverviewTier = 'kernel' | 'modeling' | 'native' | 'smoke' | 'mixed';
export type TimingOverviewTierFilter = TimingOverviewTier | 'all';
export type TimingOverviewAnalyzerFilter = TimingOverviewAnalyzerId | 'all';

export type TimingOverviewAnalyzer = {
  id: TimingOverviewAnalyzerId;
  name: string;
  pin: string;
  auxiliaryPin?: string;
};

type EvidenceStatus =
  | 'accepted-candidate'
  | 'diagnostic-costs-accepted'
  | 'quarantined'
  | 'blocked';

type SummaryMs = {
  min: number;
  median: number;
  p90: number;
  max: number;
};

type PublicationGroup = {
  group: string;
  analyzer_id: TimingOverviewAnalyzerId;
  kernel: string;
  tier: TimingOverviewTier;
  evidence_status: EvidenceStatus;
  report_rows: number;
  timed_rows: number;
  summary_ms: SummaryMs | null;
  outcomes: Record<string, number>;
  source_refs: unknown[];
  blocker?: string;
};

type TimingCase = {
  case_id: string;
  group: string;
  outcome: string;
  wall_ms: number | null;
  invocation_cost_ms: number | null;
  invocation_cost_accepted: boolean;
  latency_eligible?: boolean;
  analysis_latency_eligible: false;
  partial: boolean;
  evidence_status: string;
  source_refs: unknown[];
};

type OverheadSource = {
  group: string;
  analyzer_id: TimingOverviewAnalyzerId;
  kernel: string;
  samples_ms: number[];
  range_ms?: { low: number; high: number };
  evidence_status: string;
  source_refs: unknown[];
};

type PublicationSummary = {
  schema: string;
  publication_id: string;
  release_commit: string;
  version: string;
  publication_eligible: boolean;
  certified_timing: boolean;
  full_model_qualification: boolean;
  totals: Record<string, unknown>;
  analyzer_families: unknown[];
  groups: PublicationGroup[];
  overhead_groups: OverheadSource[];
  warm_families: unknown[];
  diagnostic_invocation_costs: Record<string, unknown>;
  quarantined_groups: unknown[];
  blocked_groups: unknown[];
  limitations: unknown[];
  source_refs: unknown[];
};

export type TimingOverviewSliceRow = {
  group: string;
  analyzerId: TimingOverviewAnalyzerId;
  analyzer: string;
  language: string;
  tier: TimingOverviewTier;
  label: string;
  status: EvidenceStatus;
  evidenceStatus: EvidenceStatus;
  coverageStatus: EvidenceStatus;
  blocker: string | null;
  reportRows: number;
  timed: number;
  untimed: number;
  partialTimedRows: number;
  quarantinedRows: number;
  excludedTimedRows: number;
  min: number | null;
  median: number | null;
  p90: number | null;
  max: number | null;
  outcomes: Record<string, number>;
  sourceRefs: unknown[];
  qualification: {
    certified: false;
    evidenceStatus: EvidenceStatus;
    analysisLatencyEligible: false;
  };
};

export type TimingOverviewAggregateRow = {
  analyzerId: TimingOverviewAnalyzerId;
  analyzer: string;
  pin: string;
  auxiliaryPin?: string;
  label: string;
  tier: TimingOverviewTierFilter;
  measuredGroups: number;
  timedGroups: number;
  plannedGroups: number;
  blockedGroups: number;
  quarantinedGroups: number;
  partialTimedRows: number;
  reportRows: number;
  timed: number;
  min: number | null;
  median: number | null;
  p90: number | null;
  max: number | null;
  status: 'measured' | 'not-measured' | 'untimed' | 'not-planned';
  coverageStatus: 'accepted-candidate' | 'diagnostic-costs-accepted' | 'partial' | 'blocked' | 'quarantined' | 'not-planned';
  blocker: string | null;
};

type PublicationCase = TimingCase;

const source = publication as unknown as PublicationSummary;
const cases = caseRows as PublicationCase[];

const analyzers: readonly TimingOverviewAnalyzer[] = [
  { id: 'bifrost', name: 'Bifrost', pin: 'v0.15.1' },
  { id: 'codeql', name: 'CodeQL CLI', pin: '2.27.2', auxiliaryPin: 'frozen packs' },
  { id: 'joern', name: 'Joern', pin: '4.0.660' },
  {
    id: 'semgrep',
    name: 'Semgrep CE',
    pin: '1.181.0',
    auxiliaryPin: 'rules 17e31e11ebac99fb7dfe1cd288f7a32151b6f3f9',
  },
  {
    id: 'opentaint',
    name: 'OpenTaint',
    pin: '0.4.6',
    auxiliaryPin: 'analyzer 2026.09.04.c51dc3e',
  },
  { id: 'infer', name: 'Infer', pin: 'v1.3.0' },
  { id: 'flowdroid', name: 'FlowDroid', pin: '2.15.1' },
  {
    id: 'pysa',
    name: 'Pysa / pyre-check',
    pin: '0.10.0',
    auxiliaryPin: 'Pyrefly 1.4.0',
  },
];

const analyzerById = new Map(analyzers.map((analyzer) => [analyzer.id, analyzer]));

function requireData(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(`invalid v0.9.2 timing publication: ${message}`);
}

function quantile(values: readonly number[], probability: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const position = probability * (sorted.length - 1);
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);
  if (lowerIndex === upperIndex) return sorted[lowerIndex] ?? null;
  const lower = sorted[lowerIndex];
  const upper = sorted[upperIndex];
  if (lower === undefined || upper === undefined) return null;
  const weight = position - lowerIndex;
  return lower * (1 - weight) + upper * weight;
}

function summarize(values: readonly number[]) {
  if (values.length === 0) {
    return { min: null, median: null, p90: null, max: null } as const;
  }
  return {
    min: Math.min(...values),
    median: quantile(values, 0.5),
    p90: quantile(values, 0.9),
    max: Math.max(...values),
  } as const;
}

function outcomeCounts(rows: readonly TimingCase[]): Record<string, number> {
  return rows.reduce<Record<string, number>>((counts, row) => {
    counts[row.outcome] = (counts[row.outcome] ?? 0) + 1;
    return counts;
  }, {});
}

function acceptedCost(row: TimingCase): number | null {
  if (!row.invocation_cost_accepted) return null;
  requireData(
    typeof row.invocation_cost_ms === 'number' &&
      Number.isFinite(row.invocation_cost_ms) && row.invocation_cost_ms > 0,
    `accepted invocation cost is missing or invalid: ${row.group}/${row.case_id}`,
  );
  return row.invocation_cost_ms;
}

function compareSummary(actual: SummaryMs | null, expected: ReturnType<typeof summarize>, group: string) {
  if (expected.min === null || expected.median === null || expected.p90 === null || expected.max === null) {
    requireData(actual === null, `${group} has a summary without accepted costs`);
    return;
  }
  requireData(actual !== null, `${group} is missing its accepted-cost summary`);
  for (const key of ['min', 'median', 'p90', 'max'] as const) {
    const got = actual[key];
    const want = expected[key];
    requireData(want !== null && Number.isFinite(got) && Math.abs(got - want) < 1e-6, `${group} ${key} summary drift`);
  }
}

requireData(source.schema === 'v092-timing-diagnostic-publication/v1', `unexpected schema ${source.schema}`);
requireData(source.publication_id === '20261123-v1', 'wrong publication ID');
requireData(source.version === '0.9.2', 'wrong release version');
requireData(source.release_commit === '86092336d8f9ca32fe9e2c4042c2dced76c1feb1', 'wrong frozen release commit');
requireData(source.publication_eligible === false, 'diagnostic publication cannot be performance-publication eligible');
requireData(source.certified_timing === false, 'diagnostic costs cannot be certified timing');
requireData(source.full_model_qualification === false, 'diagnostic costs cannot qualify full models');
requireData(source.analyzer_families.length === analyzers.length, 'analyzer family count changed');
requireData(source.groups.length === 84, `expected 84 planned cold groups, got ${source.groups.length}`);

const expectedGroupsByAnalyzer: Record<TimingOverviewAnalyzerId, number> = {
  bifrost: 20,
  codeql: 18,
  joern: 13,
  semgrep: 17,
  opentaint: 4,
  infer: 5,
  flowdroid: 4,
  pysa: 3,
};
const groupCounts = new Map<TimingOverviewAnalyzerId, number>();
for (const group of source.groups) {
  requireData(analyzerById.has(group.analyzer_id), `unknown analyzer family ${group.analyzer_id}`);
  requireData(['kernel', 'modeling', 'native', 'smoke', 'mixed'].includes(group.tier), `unknown tier ${group.tier}`);
  requireData(group.group.length > 0 && group.kernel.length > 0, 'group label is incomplete');
  requireData(
    ['accepted-candidate', 'diagnostic-costs-accepted', 'quarantined', 'blocked'].includes(group.evidence_status),
    `${group.group} has unknown evidence status ${group.evidence_status}`,
  );
  groupCounts.set(group.analyzer_id, (groupCounts.get(group.analyzer_id) ?? 0) + 1);
}
for (const analyzer of analyzers) {
  requireData(
    groupCounts.get(analyzer.id) === expectedGroupsByAnalyzer[analyzer.id],
    `${analyzer.id} cold group population changed`,
  );
}
const acceptedGroupCount = source.groups.filter(
  (group) => group.evidence_status === 'accepted-candidate' || group.evidence_status === 'diagnostic-costs-accepted',
).length;
const initialBlockedGroups = source.groups.filter((group) => group.evidence_status === 'blocked');
const initialQuarantinedGroups = source.groups.filter((group) => group.evidence_status === 'quarantined');
requireData(acceptedGroupCount === 82, `expected 82 accepted diagnostic groups, got ${acceptedGroupCount}`);
requireData(
  initialBlockedGroups.length === 1 && initialBlockedGroups[0]?.analyzer_id === 'codeql' &&
    initialBlockedGroups[0].kernel.toLowerCase().includes('swift'),
  'the single blocked cold group must remain CodeQL Swift',
);
requireData(
  initialQuarantinedGroups.length === 1 && initialQuarantinedGroups[0]?.analyzer_id === 'joern' &&
    initialQuarantinedGroups[0].kernel.toLowerCase().includes('rust'),
  'the single quarantined cold group must remain Joern Rust',
);

const groupsById = new Map<string, PublicationGroup>();
for (const group of source.groups) {
  requireData(!groupsById.has(group.group), `duplicate group ${group.group}`);
  groupsById.set(group.group, group);
}

const casesByGroup = new Map<string, TimingCase[]>();
const caseKeys = new Set<string>();
for (const row of cases) {
  requireData(groupsById.has(row.group), `case row has no cold group: ${row.group}`);
  requireData(typeof row.case_id === 'string' && row.case_id.length > 0, 'case row is missing its ID');
  const caseKey = `${row.group}\0${row.case_id}`;
  requireData(!caseKeys.has(caseKey), `duplicate case row ${row.group}/${row.case_id}`);
  caseKeys.add(caseKey);
  requireData(typeof row.invocation_cost_accepted === 'boolean', `missing cost eligibility: ${row.group}/${row.case_id}`);
  requireData(row.analysis_latency_eligible === false, `analysis-latency qualification must remain false: ${row.group}/${row.case_id}`);
  if (row.latency_eligible !== undefined) {
    requireData(row.latency_eligible === false, `legacy latency eligibility must remain false: ${row.group}/${row.case_id}`);
  }
  requireData(typeof row.partial === 'boolean', `missing partial-invocation status: ${row.group}/${row.case_id}`);
  if (row.wall_ms !== null) {
    requireData(Number.isFinite(row.wall_ms) && row.wall_ms > 0, `raw invocation duration is invalid: ${row.group}/${row.case_id}`);
  }
  if (row.invocation_cost_ms !== null) {
    requireData(Number.isFinite(row.invocation_cost_ms) && row.invocation_cost_ms > 0, `invocation cost is invalid: ${row.group}/${row.case_id}`);
  }
  if (typeof row.wall_ms === 'number' && typeof row.invocation_cost_ms === 'number') {
    requireData(Math.abs(row.wall_ms - row.invocation_cost_ms) < 1e-6, `raw/cost duration mismatch: ${row.group}/${row.case_id}`);
  }
  if (row.invocation_cost_accepted) acceptedCost(row);
  if (groupsById.get(row.group)?.evidence_status === 'quarantined') {
    requireData(!row.invocation_cost_accepted, `quarantined cost entered distribution: ${row.group}/${row.case_id}`);
  }
  const rows = casesByGroup.get(row.group) ?? [];
  rows.push(row);
  casesByGroup.set(row.group, rows);
}

const caseRowsByGroup = new Map<string, readonly TimingCase[]>();
for (const group of source.groups) {
  const rows = casesByGroup.get(group.group) ?? [];
  requireData(group.report_rows === rows.length, `${group.group} report-row count drift`);
  const accepted = rows.filter((row) => row.invocation_cost_accepted);
  const values = accepted.map((row) => acceptedCost(row) as number);
  requireData(group.timed_rows === values.length, `${group.group} accepted-cost row count drift`);
  compareSummary(group.summary_ms, summarize(values), group.group);
  const expectedOutcomes = outcomeCounts(rows);
  const outcomeKeys = new Set([...Object.keys(group.outcomes), ...Object.keys(expectedOutcomes)]);
  requireData(
    [...outcomeKeys].every((outcome) => (group.outcomes[outcome] ?? 0) === (expectedOutcomes[outcome] ?? 0)),
    `${group.group} outcome-count drift`,
  );
  caseRowsByGroup.set(group.group, rows);
}

const partialAcceptedRows = cases.filter((row) => row.partial && row.invocation_cost_accepted);
const acceptedRows = cases.filter((row) => row.invocation_cost_accepted);
const allAcceptedCosts = acceptedRows.map((row) => acceptedCost(row) as number);
const groupRows = source.groups.map((group) => {
  const analyzer = analyzerById.get(group.analyzer_id);
  if (!analyzer) throw new Error(`unknown analyzer family ${group.analyzer_id}`);
  const rows = caseRowsByGroup.get(group.group) ?? [];
  const accepted = rows.filter((row) => row.invocation_cost_accepted);
  const stats = summarize(accepted.map((row) => acceptedCost(row) as number));
  const partialTimedRows = accepted.filter((row) => row.partial).length;
  const quarantinedRows = group.evidence_status === 'quarantined' ? rows.length : 0;
  const excludedTimedRows = rows.filter((row) => !row.invocation_cost_accepted && row.invocation_cost_ms !== null).length;
  const baseLabel = `${analyzer.name} · ${group.kernel}`;
  const label = group.tier === 'mixed' ? `${baseLabel} · mixed kernel/modeling/native` : `${baseLabel} ${group.tier}`;
  return {
    group: group.group,
    analyzerId: group.analyzer_id,
    analyzer: analyzer.name,
    language: group.kernel,
    tier: group.tier,
    label,
    status: group.evidence_status,
    evidenceStatus: group.evidence_status,
    coverageStatus: group.evidence_status,
    blocker: conciseBlocker(group),
    reportRows: group.report_rows,
    timed: group.timed_rows,
    untimed: group.report_rows - group.timed_rows,
    partialTimedRows,
    quarantinedRows,
    excludedTimedRows,
    ...stats,
    outcomes: group.outcomes,
    sourceRefs: group.source_refs,
    qualification: {
      certified: false as const,
      evidenceStatus: group.evidence_status,
      analysisLatencyEligible: false as const,
    },
  } satisfies TimingOverviewSliceRow;
});

const allTiers: readonly TimingOverviewTierFilter[] = [
  'all',
  'kernel',
  'modeling',
  'native',
  'smoke',
  'mixed',
];

function conciseBlocker(group: PublicationGroup): string | null {
  if (group.evidence_status === 'blocked') {
    if (group.analyzer_id === 'codeql' && group.kernel.toLowerCase().includes('swift')) {
      return 'Pinned CodeQL Swift extractor is unavailable.';
    }
    return group.blocker ?? 'Blocked before an accepted invocation-cost observation.';
  }
  if (group.evidence_status === 'quarantined') {
    if (group.analyzer_id === 'joern' && group.kernel.toLowerCase().includes('rust')) {
      return 'Rust timing is quarantined after a semantic mismatch and excluded from accepted costs.';
    }
    return group.blocker ?? 'Quarantined costs are excluded from accepted distributions.';
  }
  return null;
}

const aggregateRows: TimingOverviewAggregateRow[] = allTiers.flatMap((tier) =>
  analyzers.map((analyzer) => {
    const planned = source.groups.filter(
      (group) => group.analyzer_id === analyzer.id && (tier === 'all' || group.tier === tier),
    );
    const selectedGroupIds = new Set(planned.map((group) => group.group));
    const rows = cases.filter((row) => selectedGroupIds.has(row.group));
    const timedRows = rows.filter((row) => row.invocation_cost_accepted);
    const times = timedRows.map((row) => acceptedCost(row) as number);
    const blocked = planned.filter((group) => group.evidence_status === 'blocked');
    const quarantined = planned.filter((group) => group.evidence_status === 'quarantined');
    const partialTimedRows = timedRows.filter((row) => row.partial).length;
    const acceptedGroupCaptures = planned.filter(
      (group) => group.evidence_status === 'accepted-candidate' || group.evidence_status === 'diagnostic-costs-accepted',
    );
    const timedGroups = planned.filter((group) => group.timed_rows > 0).length;
    const measuredGroups = acceptedGroupCaptures.length;
    const blockerText = [...new Set(planned.flatMap((group) => {
      const blocker = conciseBlocker(group);
      return blocker ? [blocker] : [];
    }))].join(' ');
    const status: TimingOverviewAggregateRow['status'] = times.length > 0 ? 'measured'
      : acceptedGroupCaptures.length > 0 ? 'untimed'
      : planned.length === 0 ? 'not-planned' : 'not-measured';
    let coverageStatus: TimingOverviewAggregateRow['coverageStatus'];
    if (planned.length === 0) coverageStatus = 'not-planned';
    else if (blocked.length === planned.length) coverageStatus = 'blocked';
    else if (quarantined.length === planned.length) coverageStatus = 'quarantined';
    else if (blocked.length > 0 || quarantined.length > 0 || partialTimedRows > 0) coverageStatus = 'partial';
    else if (planned.some((group) => group.evidence_status === 'diagnostic-costs-accepted')) coverageStatus = 'diagnostic-costs-accepted';
    else coverageStatus = 'accepted-candidate';
    return {
      analyzerId: analyzer.id,
      analyzer: analyzer.name,
      pin: analyzer.pin,
      ...(analyzer.auxiliaryPin ? { auxiliaryPin: analyzer.auxiliaryPin } : {}),
      label: `${analyzer.name} ${analyzer.pin}`,
      tier,
      measuredGroups,
      timedGroups,
      plannedGroups: planned.length,
      blockedGroups: blocked.length,
      quarantinedGroups: quarantined.length,
      partialTimedRows,
      reportRows: rows.length,
      timed: times.length,
      ...summarize(times),
      status,
      coverageStatus,
      blocker: blockerText || null,
    };
  }),
);

const summaryRows = aggregateRows.filter((row) => row.tier === 'all');

function buildLogAxis(values: readonly number[]) {
  if (values.length === 0) {
    return { domainSeconds: [0.001, 10] as const, ticksSeconds: [0.001, 0.01, 0.1, 1, 10] as const };
  }
  const minimumSeconds = Math.min(...values) / 1000;
  const maximumSeconds = Math.max(...values) / 1000;
  let lowExponent = Math.floor(Math.log10(minimumSeconds));
  let highExponent = Math.ceil(Math.log10(maximumSeconds));
  if (lowExponent === highExponent) {
    lowExponent -= 1;
    highExponent += 1;
  }
  const minimum = 10 ** lowExponent;
  const maximum = 10 ** highExponent;
  const candidates: number[] = [];
  for (let exponent = lowExponent; exponent <= highExponent; exponent += 1) {
    for (const factor of [1, 2, 5]) {
      const tick = factor * 10 ** exponent;
      if (tick >= minimum && tick <= maximum) candidates.push(tick);
    }
  }
  const ticks = candidates.length <= 6
    ? candidates
    : Array.from({ length: 6 }, (_, index) => candidates[Math.round(index * (candidates.length - 1) / 5)] as number)
      .filter((value, index, all) => all.indexOf(value) === index);
  return { domainSeconds: [minimum, maximum] as const, ticksSeconds: ticks };
}

const axis = buildLogAxis(allAcceptedCosts);

const swiftDiagnosticGroups = source.groups.filter(
  (group) => group.analyzer_id === 'joern' && group.kernel.toLowerCase().includes('swift') && group.evidence_status === 'diagnostic-costs-accepted',
);
requireData(swiftDiagnosticGroups.length === 1, 'expected one accepted Joern Swift diagnostic-cost group');
const swiftGroup = swiftDiagnosticGroups[0];
if (!swiftGroup) throw new Error('missing Joern Swift diagnostic-cost group');
const swiftRows = caseRowsByGroup.get(swiftGroup.group) ?? [];
const swiftAcceptedRows = swiftRows.filter((row) => row.invocation_cost_accepted);
const swiftCosts = swiftAcceptedRows.map((row) => acceptedCost(row) as number);
const diagnosticInvocationCosts = {
  group: swiftGroup.group,
  label: `Joern · ${swiftGroup.kernel} diagnostic invocation costs`,
  acceptedRows: swiftAcceptedRows.length,
  successfulAnalysisLatencyRows: swiftRows.filter((row) => row.analysis_latency_eligible).length,
  fullPhaseRows: swiftAcceptedRows.filter((row) => !row.partial).length,
  partialRows: swiftAcceptedRows.filter((row) => row.partial).length,
  unsupportedNoInvocationRows: swiftRows.filter((row) => row.outcome === 'unsupported' && !row.invocation_cost_accepted).length,
  inconclusiveRows: swiftAcceptedRows.filter((row) => row.outcome === 'inconclusive').length,
  ...summarize(swiftCosts),
  sourceRefs: swiftGroup.source_refs,
  acceptance: source.diagnostic_invocation_costs,
} as const;
requireData(diagnosticInvocationCosts.acceptedRows === 96, 'accepted Swift diagnostic-cost row count changed');
requireData(swiftRows.length === 108, 'Swift diagnostic group must retain all 108 declared cases');
requireData(diagnosticInvocationCosts.fullPhaseRows === 92, 'Swift full-phase cost count changed');
requireData(diagnosticInvocationCosts.partialRows === 4, 'Swift partial-cost count changed');
requireData(diagnosticInvocationCosts.successfulAnalysisLatencyRows === 0, 'Swift analysis latency must remain unqualified');
requireData(diagnosticInvocationCosts.unsupportedNoInvocationRows === 12, 'Swift unsupported no-invocation count changed');
requireData(
  swiftAcceptedRows.every((row) => row.outcome === 'inconclusive'),
  'accepted Swift costs must retain their inconclusive analysis outcomes',
);

const totalOutcomes = outcomeCounts(cases);
const blockedColdGroups = source.groups.filter((group) => group.evidence_status === 'blocked');
const quarantinedColdGroups = source.groups.filter((group) => group.evidence_status === 'quarantined');
const capturedGroups = source.groups.filter((group) => group.evidence_status !== 'blocked');
const overhead = source.overhead_groups.map((entry) => {
  const analyzer = analyzerById.get(entry.analyzer_id);
  if (!analyzer) throw new Error(`unknown overhead analyzer ${entry.analyzer_id}`);
  const range = entry.range_ms ?? {
    low: Math.min(...entry.samples_ms),
    high: Math.max(...entry.samples_ms),
  };
  return {
    group: entry.group,
    label: `${analyzer.name} / ${entry.kernel}`,
    repeats_ms: entry.samples_ms,
    range_ms: range,
    evidenceStatus: entry.evidence_status,
    sourceRefs: entry.source_refs,
  };
});
requireData(overhead.length === 9, `expected nine separate overhead groups, got ${overhead.length}`);
requireData(source.warm_families.length === 2, `expected two separate warm families, got ${source.warm_families.length}`);

const observedMax = Math.max(...allAcceptedCosts);
const summaryMedianValues = summaryRows.flatMap((row) => row.median === null ? [] : [row.median]);

export const timingOverviewV092 = {
  publicationId: source.publication_id,
  schema: source.schema,
  releaseCommit: source.release_commit,
  publicationEligible: source.publication_eligible,
  certifiedTiming: source.certified_timing,
  fullModelQualification: source.full_model_qualification,
  sourceRefs: source.source_refs,
  analyzers,
  axis,
  rows: groupRows,
  summaryRows,
  aggregateRows,
  totals: {
    reportRows: cases.length,
    timedRows: acceptedRows.length,
    untimedRows: cases.filter((row) => row.invocation_cost_ms === null).length,
    timedInconclusiveRows: acceptedRows.filter((row) => row.outcome === 'inconclusive').length,
    unsupportedUntimedRows: cases.filter((row) => row.outcome === 'unsupported' && !row.invocation_cost_accepted).length,
    capturedGroups: capturedGroups.length,
    acceptedGroups: source.groups.filter((group) => group.evidence_status === 'accepted-candidate' || group.evidence_status === 'diagnostic-costs-accepted').length,
    timedGroups: source.groups.filter((group) => group.timed_rows > 0).length,
    plannedGroups: source.groups.length,
    blockedGroups: blockedColdGroups.length,
    quarantinedGroups: quarantinedColdGroups.length,
    partialTimedRows: partialAcceptedRows.length,
    partialGroups: new Set(partialAcceptedRows.map((row) => row.group)).size,
    excludedTimedRows: cases.filter((row) => !row.invocation_cost_accepted && row.invocation_cost_ms !== null).length,
    rawQuarantinedTimedRows: cases.filter((row) => !row.invocation_cost_accepted && row.invocation_cost_ms !== null && groupsById.get(row.group)?.evidence_status === 'quarantined').length,
    outcomes: totalOutcomes,
    certifiedGroups: 0,
    publicationEligible: false,
    cpuObservationFailures: typeof source.totals.cpu_observation_failures === 'number'
      ? source.totals.cpu_observation_failures : null,
  },
  blockedGroups: blockedColdGroups.map((group) => ({ group: group.group, analyzerId: group.analyzer_id, kernel: group.kernel, blocker: conciseBlocker(group), sourceRefs: group.source_refs })),
  quarantinedGroups: quarantinedColdGroups.map((group) => ({ group: group.group, analyzerId: group.analyzer_id, kernel: group.kernel, blocker: conciseBlocker(group), sourceRefs: group.source_refs })),
  diagnosticInvocationCosts,
  overhead,
  warm: source.warm_families,
  pageUrl: '/snapshots/v0-9-2/timing-20261123-v1/',
  medianRange: {
    min: Math.min(...summaryMedianValues),
    max: Math.max(...summaryMedianValues),
  },
  observedMax,
} as const;

export function timingOverviewRows(
  analyzer: TimingOverviewAnalyzerFilter = 'all',
  tier: TimingOverviewTierFilter = 'all',
): readonly TimingOverviewSliceRow[] {
  return timingOverviewV092.rows.filter(
    (row) =>
      (analyzer === 'all' || row.analyzerId === analyzer) &&
      (tier === 'all' || row.tier === tier),
  );
}

export function timingOverviewAggregateRows(
  analyzer: TimingOverviewAnalyzerFilter = 'all',
  tier: TimingOverviewTierFilter = 'all',
): readonly TimingOverviewAggregateRow[] {
  return timingOverviewV092.aggregateRows.filter(
    (row) =>
      row.tier === tier &&
      (analyzer === 'all' || row.analyzerId === analyzer),
  );
}

export function timingPosition(ms: number): number {
  if (!Number.isFinite(ms) || ms <= 0) {
    throw new RangeError('timing must be finite and positive');
  }

  const seconds = ms / 1000;
  const [minimum, maximum] = timingOverviewV092.axis.domainSeconds;
  if (seconds < minimum || seconds > maximum) {
    throw new RangeError(
      `timing must be within ${minimum}..${maximum} seconds: ${ms} ms`,
    );
  }

  return (
    ((Math.log(seconds) - Math.log(minimum)) /
      (Math.log(maximum) - Math.log(minimum))) *
    100
  );
}

export function formatTiming(ms: number | null): string {
  if (ms === null) return '—';
  if (!Number.isFinite(ms) || ms < 0) {
    throw new RangeError('timing must be finite and non-negative');
  }
  if (ms > 0 && ms < 1) return '<1 ms';
  const roundedMs = Math.round(ms);
  if (roundedMs < 1000) return `${roundedMs} ms`;

  const seconds = (ms / 1000).toFixed(2).replace(/\.?0+$/, '');
  return `${seconds} s`;
}

export function formatAxisTick(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds <= 0) {
    throw new RangeError('axis tick must be finite and positive');
  }
  const ms = seconds * 1000;
  if (ms < 1) return `${Number(ms.toPrecision(2))} ms`;
  return formatTiming(ms);
}

import {
  timingSupplementV092,
  type TimingSupplementSlice,
} from './timing-supplement-v092.ts';
import timingPlan from '../../../reports/timing/v0.9.2/20261113-02/plan.json' with { type: 'json' };
import caseRows from '../../../reports/timing/v0.9.2/20261113-02/reconciliation-v1/cases.json' with { type: 'json' };

export type TimingOverviewAnalyzerId =
  | 'bifrost'
  | 'codeql'
  | 'joern'
  | 'semgrep'
  | 'opentaint'
  | 'infer'
  | 'flowdroid'
  | 'pysa';
export type TimingOverviewTier = 'kernel' | 'modeling' | 'native' | 'smoke';
export type TimingOverviewTierFilter = TimingOverviewTier | 'all';
export type TimingOverviewAnalyzerFilter = TimingOverviewAnalyzerId | 'all';

export type TimingOverviewAnalyzer = {
  id: TimingOverviewAnalyzerId;
  name: string;
  pin: string;
  auxiliaryPin?: string;
};

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

type TimingCase = {
  case_id: string;
  group: string;
  outcome: string;
  wall_ms: number | null;
};

type PlannedGroup = {
  id: string;
  family: TimingOverviewAnalyzerId;
  kind: 'cold' | 'overhead';
  status: string;
  blocker?: string;
};

type TimingPlan = { groups: PlannedGroup[] };

const cases = caseRows as TimingCase[];
const plan = timingPlan as TimingPlan;

function tierForGroup(group: string): TimingOverviewTier {
  if (group.endsWith('-smoke')) return 'smoke';
  if (group.endsWith('-modeling')) return 'modeling';
  if (group.endsWith('-native')) return 'native';
  return 'kernel';
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

function conciseBlocker(blocker: string): string {
  if (blocker.includes('Scala Maven materialization')) {
    return 'Pinned Scala Maven materialization must be restored and verified.';
  }
  if (blocker.includes('launcher digest differs')) {
    return 'Pinned /usr/bin/java or javac digest differs on this OS.';
  }
  if (blocker.includes('Exact v0.9.2 runtime closure')) {
    return 'Exact v0.9.2 runtime closure is missing from its bound paths; restoration and verification are pending.';
  }
  return blocker;
}

const coldPlan = plan.groups.filter((group) => group.kind === 'cold');
const coldPlanById = new Map(coldPlan.map((group) => [group.id, group]));
const capturedGroupIds = new Set(timingSupplementV092.coldSlices.map((slice) => slice.group));
const casesByGroup = new Map<string, TimingCase[]>();

for (const row of cases) {
  if (!Number.isFinite(row.wall_ms) && row.wall_ms !== null) {
    throw new Error(`non-finite timing for ${row.group}/${row.case_id}`);
  }
  if (!coldPlanById.has(row.group)) {
    throw new Error(`case rows have no planned cold group: ${row.group}`);
  }
  const groupRows = casesByGroup.get(row.group) ?? [];
  groupRows.push(row);
  casesByGroup.set(row.group, groupRows);
}

for (const group of capturedGroupIds) {
  if (!casesByGroup.has(group)) {
    throw new Error(`captured cold group has no case rows: ${group}`);
  }
}

export type TimingOverviewSliceRow = Omit<
  TimingSupplementSlice,
  'descendantContainment'
> & {
  analyzerId: TimingOverviewAnalyzerId;
  analyzer: string;
  language: string;
  tier: TimingOverviewTier;
  label: string;
  untimed: number;
};

const sliceDisplay: Record<string, Omit<TimingOverviewSliceRow, keyof TimingSupplementSlice | 'untimed'>> = {
  'bifrost-c-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'C', tier: 'kernel', label: 'Bifrost · C kernel' },
  'bifrost-cpp-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'C++', tier: 'kernel', label: 'Bifrost · C++ kernel' },
  'bifrost-csharp-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'C#', tier: 'kernel', label: 'Bifrost · C# kernel' },
  'bifrost-go-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Go', tier: 'kernel', label: 'Bifrost · Go kernel' },
  'bifrost-java-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Java', tier: 'kernel', label: 'Bifrost · Java kernel' },
  'bifrost-java-modeling': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Java', tier: 'modeling', label: 'Bifrost · Java modeling' },
  'bifrost-java-native': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Java', tier: 'native', label: 'Bifrost · Java native' },
  'bifrost-javascript-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'JavaScript', tier: 'kernel', label: 'Bifrost · JavaScript kernel' },
  'bifrost-javascript-modeling': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'JavaScript', tier: 'modeling', label: 'Bifrost · JavaScript modeling' },
  'bifrost-javascript-native': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'JavaScript', tier: 'native', label: 'Bifrost · JavaScript native' },
  'bifrost-kotlin-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Kotlin', tier: 'kernel', label: 'Bifrost · Kotlin kernel' },
  'bifrost-php-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'PHP', tier: 'kernel', label: 'Bifrost · PHP kernel' },
  'bifrost-python-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Python', tier: 'kernel', label: 'Bifrost · Python kernel' },
  'bifrost-python-modeling': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Python', tier: 'modeling', label: 'Bifrost · Python modeling' },
  'bifrost-python-native': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Python', tier: 'native', label: 'Bifrost · Python native' },
  'bifrost-ruby-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Ruby', tier: 'kernel', label: 'Bifrost · Ruby kernel' },
  'bifrost-rust-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'Rust', tier: 'kernel', label: 'Bifrost · Rust kernel' },
  'bifrost-smoke': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'mixed languages', tier: 'smoke', label: 'Bifrost · mixed languages smoke' },
  'bifrost-typescript-kernel': { analyzerId: 'bifrost', analyzer: 'Bifrost', language: 'TypeScript', tier: 'kernel', label: 'Bifrost · TypeScript kernel' },
  'infer-c-kernel': { analyzerId: 'infer', analyzer: 'Infer', language: 'C', tier: 'kernel', label: 'Infer · C kernel' },
  'infer-cpp-kernel': { analyzerId: 'infer', analyzer: 'Infer', language: 'C++', tier: 'kernel', label: 'Infer · C++ kernel' },
};

const sliceRows: TimingOverviewSliceRow[] = timingSupplementV092.coldSlices.map((slice) => {
  const display = sliceDisplay[slice.group];
  if (!display) {
    throw new Error(`missing timing overview display metadata: ${slice.group}`);
  }

  return {
    group: slice.group,
    ...display,
    reportRows: slice.reportRows,
    timed: slice.timed,
    untimed: slice.reportRows - slice.timed,
    min: slice.min,
    median: slice.median,
    p90: slice.p90,
    max: slice.max,
    outcomes: slice.outcomes,
    qualification: slice.qualification,
  };
});

export type TimingOverviewAggregateRow = {
  analyzerId: TimingOverviewAnalyzerId;
  analyzer: string;
  pin: string;
  auxiliaryPin?: string;
  label: string;
  tier: TimingOverviewTierFilter;
  measuredGroups: number;
  plannedGroups: number;
  blockedGroups: number;
  reportRows: number;
  timed: number;
  min: number | null;
  median: number | null;
  p90: number | null;
  max: number | null;
  status: 'measured' | 'not-measured' | 'untimed' | 'not-planned';
  blocker: string | null;
};

const allTiers: readonly TimingOverviewTierFilter[] = [
  'all',
  'kernel',
  'modeling',
  'native',
  'smoke',
];

const aggregateRows: TimingOverviewAggregateRow[] = allTiers.flatMap((tier) =>
  analyzers.map((analyzer) => {
    const plannedGroups = coldPlan.filter(
      (group) =>
        group.family === analyzer.id &&
        (tier === 'all' || tierForGroup(group.id) === tier),
    );
    const capturedGroups = plannedGroups.filter((group) => capturedGroupIds.has(group.id));
    const blockedGroups = plannedGroups.filter((group) => group.status === 'blocked');
    const rows = plannedGroups.flatMap((group) => casesByGroup.get(group.id) ?? []);
    const timings = rows.flatMap((row) =>
      typeof row.wall_ms === 'number' ? [row.wall_ms] : [],
    );
    const blockerText = [...new Set(blockedGroups.flatMap((group) =>
      group.blocker ? [conciseBlocker(group.blocker)] : [],
    ))].join(' ');

    return {
      analyzerId: analyzer.id,
      analyzer: analyzer.name,
      pin: analyzer.pin,
      ...(analyzer.auxiliaryPin ? { auxiliaryPin: analyzer.auxiliaryPin } : {}),
      label: `${analyzer.name} ${analyzer.pin}`,
      tier,
      measuredGroups: capturedGroups.length,
      plannedGroups: plannedGroups.length,
      blockedGroups: blockedGroups.length,
      reportRows: rows.length,
      timed: timings.length,
      ...summarize(timings),
      status: timings.length > 0 ? 'measured'
        : capturedGroups.length > 0 ? 'untimed'
        : plannedGroups.length === 0 ? 'not-planned' : 'not-measured',
      blocker: blockerText || null,
    };
  }),
);

const summaryRows = aggregateRows.filter((row) => row.tier === 'all');
const totalPlanGroups = coldPlan.length;
const observedContentionGroups = timingSupplementV092.coldSlices
  .filter((slice) => slice.qualification.contention_observed)
  .map((slice) => slice.group);
const quietGatePassedGroups = timingSupplementV092.coldSlices
  .filter((slice) => slice.qualification.initial_quiet_gate_passed)
  .map((slice) => slice.group);
const cpuObservationFailures = [
  ...timingSupplementV092.coldSlices.map((slice) => slice.qualification),
  ...timingSupplementV092.overhead.map((entry) => entry.qualification),
].reduce(
  (total, qualification) => total + qualification.observation_failures,
  0,
);

export const timingOverviewV092 = {
  axis: {
    domainSeconds: [0.25, 10],
    ticksSeconds: [0.25, 0.5, 1, 2, 4, 8],
  },
  analyzers,
  rows: sliceRows,
  summaryRows,
  aggregateRows,
  totals: {
    reportRows: cases.length,
    timedRows: cases.filter((row) => typeof row.wall_ms === 'number').length,
    untimedRows: cases.filter((row) => row.wall_ms === null).length,
    timedInconclusiveRows: cases.filter((row) => typeof row.wall_ms === 'number' && row.outcome === 'inconclusive').length,
    unsupportedUntimedRows: cases.filter((row) => row.wall_ms === null && row.outcome === 'unsupported').length,
    capturedGroups: capturedGroupIds.size,
    timedGroups: new Set(cases.filter((row) => typeof row.wall_ms === 'number').map((row) => row.group)).size,
    plannedGroups: totalPlanGroups,
    blockedColdGroups: timingSupplementV092.totals.blockedColdGroups,
    certifiedGroups: timingSupplementV092.totals.certifiedGroups,
    publicationEligible: timingSupplementV092.publicationEligible,
    observedContentionGroups,
    quietGatePassedGroups,
    cpuObservationFailures,
  },
  pageUrl: timingSupplementV092.pageUrl,
  overhead: timingSupplementV092.overhead,
  medianRange: {
    min: Math.min(
      ...summaryRows.flatMap((row) => (row.median === null ? [] : [row.median])),
    ),
    max: Math.max(
      ...summaryRows.flatMap((row) => (row.median === null ? [] : [row.median])),
    ),
  },
  observedMax: Math.max(
    ...summaryRows.flatMap((row) => (row.max === null ? [] : [row.max])),
  ),
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
  const roundedMs = Math.round(ms);
  if (roundedMs < 1000) return `${roundedMs} ms`;

  const seconds = (ms / 1000).toFixed(2).replace(/\.?0+$/, '');
  return `${seconds} s`;
}

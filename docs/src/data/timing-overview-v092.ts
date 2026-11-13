import {
  timingSupplementV092,
  type TimingSupplementSlice,
} from './timing-supplement-v092.ts';

export type TimingOverviewAnalyzer = 'Bifrost' | 'Infer';
export type TimingOverviewTier = 'kernel' | 'modeling' | 'native' | 'smoke';
export type TimingOverviewLanguage =
  | 'C'
  | 'C++'
  | 'C#'
  | 'Go'
  | 'Java'
  | 'JavaScript'
  | 'Kotlin'
  | 'PHP'
  | 'Python'
  | 'Ruby'
  | 'Rust'
  | 'TypeScript'
  | 'mixed languages';

export type TimingOverviewAnalyzerFilter = TimingOverviewAnalyzer | 'all';
export type TimingOverviewTierFilter = TimingOverviewTier | 'all';

type SliceDisplay = {
  analyzer: TimingOverviewAnalyzer;
  language: TimingOverviewLanguage;
  tier: TimingOverviewTier;
  label: string;
};

const sliceDisplay: Record<string, SliceDisplay> = {
  'bifrost-c-kernel': {
    analyzer: 'Bifrost',
    language: 'C',
    tier: 'kernel',
    label: 'Bifrost · C kernel',
  },
  'bifrost-cpp-kernel': {
    analyzer: 'Bifrost',
    language: 'C++',
    tier: 'kernel',
    label: 'Bifrost · C++ kernel',
  },
  'bifrost-csharp-kernel': {
    analyzer: 'Bifrost',
    language: 'C#',
    tier: 'kernel',
    label: 'Bifrost · C# kernel',
  },
  'bifrost-go-kernel': {
    analyzer: 'Bifrost',
    language: 'Go',
    tier: 'kernel',
    label: 'Bifrost · Go kernel',
  },
  'bifrost-java-kernel': {
    analyzer: 'Bifrost',
    language: 'Java',
    tier: 'kernel',
    label: 'Bifrost · Java kernel',
  },
  'bifrost-java-modeling': {
    analyzer: 'Bifrost',
    language: 'Java',
    tier: 'modeling',
    label: 'Bifrost · Java modeling',
  },
  'bifrost-java-native': {
    analyzer: 'Bifrost',
    language: 'Java',
    tier: 'native',
    label: 'Bifrost · Java native',
  },
  'bifrost-javascript-kernel': {
    analyzer: 'Bifrost',
    language: 'JavaScript',
    tier: 'kernel',
    label: 'Bifrost · JavaScript kernel',
  },
  'bifrost-javascript-modeling': {
    analyzer: 'Bifrost',
    language: 'JavaScript',
    tier: 'modeling',
    label: 'Bifrost · JavaScript modeling',
  },
  'bifrost-javascript-native': {
    analyzer: 'Bifrost',
    language: 'JavaScript',
    tier: 'native',
    label: 'Bifrost · JavaScript native',
  },
  'bifrost-kotlin-kernel': {
    analyzer: 'Bifrost',
    language: 'Kotlin',
    tier: 'kernel',
    label: 'Bifrost · Kotlin kernel',
  },
  'bifrost-php-kernel': {
    analyzer: 'Bifrost',
    language: 'PHP',
    tier: 'kernel',
    label: 'Bifrost · PHP kernel',
  },
  'bifrost-python-kernel': {
    analyzer: 'Bifrost',
    language: 'Python',
    tier: 'kernel',
    label: 'Bifrost · Python kernel',
  },
  'bifrost-python-modeling': {
    analyzer: 'Bifrost',
    language: 'Python',
    tier: 'modeling',
    label: 'Bifrost · Python modeling',
  },
  'bifrost-python-native': {
    analyzer: 'Bifrost',
    language: 'Python',
    tier: 'native',
    label: 'Bifrost · Python native',
  },
  'bifrost-ruby-kernel': {
    analyzer: 'Bifrost',
    language: 'Ruby',
    tier: 'kernel',
    label: 'Bifrost · Ruby kernel',
  },
  'bifrost-rust-kernel': {
    analyzer: 'Bifrost',
    language: 'Rust',
    tier: 'kernel',
    label: 'Bifrost · Rust kernel',
  },
  'bifrost-smoke': {
    analyzer: 'Bifrost',
    language: 'mixed languages',
    tier: 'smoke',
    label: 'Bifrost · mixed languages smoke',
  },
  'bifrost-typescript-kernel': {
    analyzer: 'Bifrost',
    language: 'TypeScript',
    tier: 'kernel',
    label: 'Bifrost · TypeScript kernel',
  },
  'infer-c-kernel': {
    analyzer: 'Infer',
    language: 'C',
    tier: 'kernel',
    label: 'Infer · C kernel',
  },
  'infer-cpp-kernel': {
    analyzer: 'Infer',
    language: 'C++',
    tier: 'kernel',
    label: 'Infer · C++ kernel',
  },
};

export type TimingOverviewRow = Omit<TimingSupplementSlice, 'descendantContainment'> &
  SliceDisplay & {
    untimed: number;
  };

const rows: TimingOverviewRow[] = timingSupplementV092.coldSlices.map(
  (slice) => {
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
  },
);

export const timingOverviewV092 = {
  axis: {
    domainSeconds: [0.25, 10],
    ticksSeconds: [0.25, 0.5, 1, 2, 4, 8],
  },
  rows,
  totals: timingSupplementV092.totals,
  pageUrl: timingSupplementV092.pageUrl,
  overhead: timingSupplementV092.overhead,
  medianRange: {
    min: Math.min(
      ...rows.flatMap((row) => (row.median === null ? [] : [row.median])),
    ),
    max: Math.max(
      ...rows.flatMap((row) => (row.median === null ? [] : [row.median])),
    ),
  },
  observedMax: Math.max(
    ...rows.flatMap((row) => (row.max === null ? [] : [row.max])),
  ),
} as const;

export function timingOverviewRows(
  analyzer: TimingOverviewAnalyzerFilter = 'all',
  tier: TimingOverviewTierFilter = 'all',
): readonly TimingOverviewRow[] {
  return timingOverviewV092.rows.filter(
    (row) =>
      (analyzer === 'all' || row.analyzer === analyzer) &&
      (tier === 'all' || row.tier === tier),
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

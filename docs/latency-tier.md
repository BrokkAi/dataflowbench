# Latency-characterization tier

This document is the **preregistration artifact** for a descriptive latency
tier: per-case wall-clock, published as medians and distributions per slice,
beside — and never inside — the correctness scorecards. It merges before any
timing is captured, before any runner writes a timestamp, and before any number
derived from one is published.

Nothing in this document is a result. It is a contract about what will be
measured, stated in advance so that the measurement cannot later be shaped
around what the measurement produced.

It is the characterization half of issue #89. The instrumentation half —
capturing timestamps at the boundaries this document names and retaining them
in the raw artifacts — is issue #90, lands separately, and changes nothing
written here.

## Motivation

The v0.5.0 evidence re-run made the shape of the cost visible: wall-clock was
dominated by the CodeQL slices, where every case pays for database extraction
with traced compiles, while the Bifrost slices — post-0.10.7, with zero runner
errors — were the fastest. Latency is a real dimension of analyzer capability,
and it is the core thesis of IDE-resident analysis: an engine that answers in
tens of milliseconds is usable in a keystroke loop and an engine that answers
in minutes is a batch job, whatever their scorecards say.

It is also the dimension this project is least entitled to publish casually.
DataFlowBench is published by the vendor of the engine the re-run observed to
be fastest. A latency page assembled after the numbers were known — with its
phase boundaries, its exclusions, and its aggregation chosen afterwards — would
deserve exactly the skepticism it would get. So the contract is fixed here,
while every number is still unmeasured, with the same discipline every other
tier gets: what is timed, where the phase cuts fall, what is excluded, and how
the numbers may and may not be read, all committed before the first timestamp
exists.

## What the tier is

### Descriptive characterization, not a score

Latency is published as a **descriptive tier**: per-case wall-clock,
aggregated as medians and distributions per slice (per adapter, per language,
per population), presented beside the correctness scorecards as its own
section.

The load-bearing rules, stated as bluntly as they will ever need to be read:

- **No latency value ever influences a correctness outcome.** Not as a
  timeout-derived verdict, not as a tie-breaker, not as a weight. The
  correctness pipeline does not read timing fields, and issue #90's
  instrumentation is additive metadata that the scoring path never consults.
- **Latency is never pooled with correctness.** No combined score, no
  "efficiency-adjusted" number, no leaderboard that ranks a blend. "Correct
  but slow" and "fast but wrong" must remain independently visible, because
  collapsing them into one number is precisely how a vendor-published
  benchmark would flatter a fast engine.
- **A latency number is a property of a run, not of a case.** Cases stay
  correctness-only: no `case.json` carries a latency assertion, threshold, or
  budget, and no case outcome vocabulary gains a timing-derived member.

### The unit of observation

The unit is the **per-case analyzer invocation**: the wall-clock of the
subprocess (or subprocesses) the runner spawns to analyze one case's
workspace. The case population is the sample. There are no repeated trials, no
warm-up iterations, and no micro-benchmarking harness: the distribution over a
slice's cases — which the population provides for free — is the statistics,
and anything finer is analyzer-internal profiling, which this tier does not
do.

That choice has a consequence worth stating in advance: per-case wall-clock at
this granularity includes per-invocation fixed costs — JVM start-up, extractor
initialization, interpreter start — that a long-lived deployment of the same
engine would amortize. The tier does not correct for this. It characterizes
what the benchmark actually runs, invocation shapes included, and the
per-adapter table below records exactly what each invocation shape charges to
each number so that a reader can see the fixed costs rather than guess at
them.

## The decomposition rule

> **Semi-granular, at adapter-observable subprocess boundaries only.** A phase
> is timed if and only if the adapter already invokes it as a separate
> subprocess. The benchmark never instruments analyzer internals, never
> patches an upstream tool, and never infers a phase boundary a subprocess
> boundary does not expose.

Two corollaries:

1. **Unequal granularity is declared, not hidden.** The adapters do not expose
   the same boundaries, so the tiers' rows are not equally decomposed — CodeQL
   yields phases where Bifrost yields one number — and the table below is the
   declaration. Papering over the difference (by summing CodeQL's phases into
   a total and pretending every row is one number of the same kind, or by
   guessing phase splits for the single-invocation tools) would misdescribe
   both.
2. **Phases compare within an adapter; totals compare across adapters.** A
   CodeQL `extract` number and a Joern total are not the same kind of
   quantity. Cross-adapter reading uses each adapter's whole-invocation
   wall-clock, with the granularity caveat attached; per-phase numbers exist
   to decompose one adapter's own cost, not to race one adapter's phase
   against another's total.

A tool that itself emits phase timings in its own output is a third source,
distinct from both: those are **tool-reported** numbers, retained verbatim in
the raw artifact as the tool wrote them, labelled as the tool's own claim, and
never summed with or substituted for the adapter-observed wall-clock.

### Per-adapter granularity

Grounded in the invocation shapes the runners actually use today, which are
pinned by tests. The granularity actually achieved per adapter is part of this
preregistration.

| Adapter | Subprocesses per case | Phases timed | What each number contains |
| --- | --- | --- | --- |
| CodeQL 2.26.4 | 2 — `database create`, then `database analyze` | `extract`, `analyze` | `extract` is database creation **including traced compiles** — a real cost a user waits for, attributed to extraction and never to query evaluation. `analyze` is query evaluation *and* SARIF interpretation, which the CLI performs inside one subprocess as invoked. |
| Joern 4.0.614 | 1 — `joern --script` with per-case parameters | `total` | One number, honestly labelled: frontend import, CPG construction, and query-script execution happen inside a single JVM invocation, and the boundary between them is not adapter-observable. **JVM start-up policy: cold, per case** — each case is a fresh JVM in a fresh scratch directory, and that start-up cost is inside the number, stated rather than hidden. |
| Bifrost v0.10.7 | 1 — one policy-CLI invocation | `total` | A single CLI invocation is indivisible from the adapter's vantage: one number per case. |
| Semgrep CE 1.175.0 | 1 — one `semgrep scan` | `total` | Same: one number per case, interpreter start-up included. |

Notes that bound the table:

- **CodeQL's finer three-way split is conditional, and the condition is
  named.** The idealized decomposition — extraction vs. query evaluation vs.
  SARIF interpretation — is only adapter-observable if the analyze step is
  performed through the CLI's own separate plumbing subcommands
  (`database run-queries`, then `database interpret-results`) instead of the
  single `database analyze` call the adapters make today. Whether issue #90
  adopts that split is an instrumentation decision made there; **this document
  preregisters the boundary rule, not the invocation shape.** If the split is
  adopted, `analyze` becomes `query` and `interpret` and the change is
  recorded by a dated amendment here; until then, `analyze` is one phase and
  is labelled as containing both.
- **Joern's boundary could only be exposed by the benchmark's own script
  timestamping itself**, which is not a subprocess boundary and is not done by
  this tier. If a future pinned Joern invocation shape genuinely separates
  import from query at the process level, the row is refined by amendment.
- **Tool-reported phase timings** (for example, Semgrep's own timing output if
  a future instrumentation decision enables it) are retained under the
  tool-reported rule above. Nothing in this document turns them on.

## Exclusions

The tier times the analyzer, not the benchmark. Excluded from every latency
number, by construction rather than by subtraction:

- **Harness compile time.** `cargo build` of the runner is benchmark
  infrastructure.
- **Fixture materialization.** Copying fixture files into the per-case scratch
  workspace, and synthesizing the Cargo manifest the Rust populations require,
  happen before the analyzer subprocess is spawned and are outside the timed
  window.
- **Report normalization and reconciliation.** Parsing SARIF or JSON output,
  anchor matching, outcome derivation, and report writing are runner work,
  performed in-process after the subprocess exits. (For CodeQL this cuts at
  the subprocess boundary: SARIF *rendering* inside `database analyze` is in
  the `analyze` number because the CLI performs it there; the runner's own
  *reading* of that SARIF is not.)
- **Validation and freeze machinery.** `validate`, `validate-reports`,
  `validate-freeze`, and digest computation are not analyzer time.
- **The version witness.** Each runner reads the pinned binary's version
  banner once per run to witness tool identity. That read is run
  identification, not case analysis, and is outside every per-case number.

### Cache states, declared per adapter

A wall-clock number is only interpretable if the cache state behind it is
stated. Each latency-bearing run declares, per adapter, the cache posture it
ran under — the following are the caches known to matter, and the declaration
is of their state, not a promise to defeat them:

- **CodeQL**: the query-pack and compilation cache (pre-fetched packs versus
  first-run downloads; compiled versus cold query plans — the adapters pass
  `--rerun`, which forces re-evaluation but not query recompilation), and the
  state of any compiler toolchain caches the traced extractors invoke.
- **Joern**: no cross-case cache by construction — each case's CPG is built in
  its own scratch directory precisely so no case can observe another's — but
  the JVM and frontend distributions are on local disk, and that is the stated
  baseline.
- **Bifrost**: whatever index or cache state the pinned CLI maintains;
  declared as found.
- **Semgrep**: rule parsing is per-invocation on the pinned CE build; the
  vendored ruleset is on local disk.
- **Cross-cutting**: OS page cache warmth is not controlled and not claimed to
  be; the sequential-run discipline below is the only isolation asserted.

A run that cannot state a cache posture states that it cannot, which is itself
the declaration.

## Environment scope

Every latency-bearing report carries an **environment stamp**: hardware model,
OS and version, and logical CPU count, recorded once per run beside the
existing tool-identity witness.

The stamp is a scope, not a garnish: **latency numbers are comparable within
one run's environment and are not comparable across machines.** All published
runs to date execute on a single maintainer machine, and that single-machine
caveat travels with every number. A median from one environment set beside a
median from another is two facts about two machines, not a ranking of two
engines, and no publication of this tier presents cross-environment numbers in
one table without saying so in the table.

## Measurement hygiene

The standing sequential-run discipline — runners execute one at a time, never
concurrently, because each sweeps its whole report directory and two runners
rewriting retained evidence at once race — **doubles as this tier's
measurement hygiene**: no analyzer competes for the machine while another is
being timed. The discipline is already the documented operating rule for every
population; this tier adds a reason to keep it, not a new rule. A run known to
have violated it has honest correctness evidence and unusable latency
evidence, and its timing fields are excluded from publication rather than
quietly averaged in.

## Reporting

- **Home of the evidence.** Per-case timings live in the retained raw
  artifacts, captured by issue #90's instrumentation at the boundaries this
  document fixes. Reports remain frozen bytes; timing fields are additive
  metadata whose absence in pre-existing artifacts is not an error.
- **Aggregation.** Per slice (adapter × language × population): median,
  minimum, maximum, and quartiles of per-case wall-clock, per phase where the
  adapter's row has phases. No mean is headlined — the distributions are
  expected to be skewed by per-invocation fixed costs — and no aggregate ever
  crosses the granularity rule above.
- **Presentation.** A latency section stands beside the correctness
  scorecards, per adapter and per language, carrying its environment stamp,
  its cache declarations, and its granularity caveats on the same page as its
  numbers. It is never a column inside a correctness table.
- **Publication is freeze-gated.** Published latency numbers come only from
  validated freeze manifests that bind latency-bearing reports, exactly as
  every other published number does. The site page for this tier follows the
  first such freeze and is out of scope for this document beyond the rules
  above.

## Non-goals

- **No micro-benchmarking.** No repeated trials, no steady-state harness, no
  statistics beyond what the case population already provides.
- **No analyzer-internal profiling.** No instrumentation, patching, or
  tracing of upstream tools; the subprocess boundary is the deepest cut.
- **No latency assertions in cases.** `case.json` stays correctness-only; no
  schema change adds a timing expectation to any case.
- **No thresholds, budgets, or pass/fail.** The tier describes; it never
  judges. Interpretation beyond the descriptive statistics above is a future
  preregistration, not an amendment to this one.

## Invariants

- No latency value ever influences a correctness outcome, in any tier, in any
  release.
- Latency and correctness are never pooled, never averaged, and never
  presented as one number or one ranking.
- Per-adapter granularity is unequal, declared in this document's table, and
  never papered over; phases compare within an adapter, totals across
  adapters.
- Adapter-observed wall-clock and tool-reported timings are distinct sources
  and are never summed or substituted for each other.
- Latency numbers are environment-scoped and are not compared across machines
  without the comparison being labelled as cross-environment.
- Timing capture is additive metadata: pre-existing frozen artifacts without
  it remain valid, and no validator conditions a correctness verdict on a
  timing field.
- Latency-bearing runs execute under the sequential-run discipline, or their
  timing fields are not published.
- Published latency numbers come only from validated freeze manifests.

## Governance

**The amendment contract of the
[challenge tier](challenge-tier.md#preregistration-and-immutability) applies
to this document verbatim**, as it does to the
[modeling matrix](modeling-matrix.md) and the
[tool-native profile](native-profile.md). From the moment the first
latency-bearing raw artifact is retained, the decomposition rule, the
per-adapter granularity table, the exclusion list, and the reporting rules
above are **immutable**: a defect is corrected by a dated amendment, never by
a silent edit, and a phase boundary is never moved after numbers exist on both
sides of it.

Two amendment triggers are anticipated by name, so that neither arrives
looking like a surprise: a CodeQL invocation-shape change that splits
`analyze` into `query` and `interpret`, and a pinned-Joern change that exposes
the import/query boundary at the process level. Each is a granularity
refinement recorded with the run that first uses it; neither retroactively
redescribes any earlier number.

## Amendments

Amendments are dated, state what changed and which adapters and phases they
touch, name the freezes they invalidate, and land as their own commits.

Their numbers continue the repository's **single** amendment sequence rather
than restarting per document: A1 is in
[the challenge tier](challenge-tier.md#amendments), A2–A5 and A9 are in
[the modeling matrix](modeling-matrix.md#amendments), and A6–A8 and A10 are in
[the tool-native profile](native-profile.md#amendments). This document joins
that sequence — its first amendment takes the next unused number in the
repository, not A1 — so that an amendment identifier names exactly one
amendment wherever it is cited.

None yet.

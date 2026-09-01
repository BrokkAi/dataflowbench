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
| Infer v1.3.0 | 2 — `infer capture`, then `infer analyze` | `capture`, `analyze` | Added by [Amendment A12](#a12--2026-09-01-the-four-adapters-added-in-v060-take-their-granularity-rows). `capture` is the traced compile into Infer's own intermediate representation — the same cost, and the same attribution, as CodeQL's `extract`. `analyze` is Pulse evaluation *and* SARIF emission, which the pinned CLI performs inside one subprocess as invoked. |
| OpenTaint `analyzer/2026.08.27.17eb0fe` | 1 — one analyzer-jar invocation | `total` | Added by Amendment A12. One JVM invocation per case, indivisible from the adapter's vantage. **JVM start-up policy: cold, per case**, and that start-up is inside the number. |
| FlowDroid 2.15.1 | 1 — one command-line analyzer invocation | `total` | Added by Amendment A12. One number per case, cold JVM start-up included. **The per-case APK materialization the released CLI requires is *not* in the number**: the D8 dex translation and APK assembly are fixture materialization, performed before the analyzer subprocess is spawned, and are excluded by the rule below exactly as every other adapter's workspace preparation is. |
| Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0) | 1 — one `pyre analyze` invocation | `total` | Added by Amendment A12. The pinned client drives the Pyrefly front end and the taint analysis inside a single invocation the adapter cannot observe as separate subprocesses, so the front-end cost is inside the one number rather than split out. Interpreter start-up included. |

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
- **Infer** (Amendment A12): no cross-case cache — each case gets its own
  scratch workspace and its own `--results-dir`, so no case can observe
  another's capture database; the pinned distribution is on local disk.
- **OpenTaint** (Amendment A12): no cross-case cache; one cold JVM per case
  over a per-case scratch workspace, with the pinned jar on local disk.
- **FlowDroid** (Amendment A12): no cross-case cache; one cold JVM per case
  over a per-case scratch workspace holding that case's freshly materialized
  APK, with the pinned jar and the Android platform jar on local disk.
- **Pysa** (Amendment A12): no cross-case cache; each case gets its own
  scratch project, its own `.pyre_configuration`, and its own `pyrefly.toml`,
  so no case can observe another's front-end resolution state. The pinned
  client, analysis binary, and Pyrefly build are on local disk.
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

### First publication

Dated so that the tier's publication history is as auditable as its contract.

| Date | Freeze | What was published | Where |
| --- | --- | --- | --- |
| 2026-09-01 | `v0.6.0` | Per-slice and per-adapter medians, quartiles, minima and maxima of per-case wall-clock over 2657 timed analyzer invocations on eight adapters, with phase splits for the two adapters whose rows declare them (CodeQL, Infer) and one whole-invocation number for the six that do not. One environment stamp, displayed verbatim. | `docs/src/content/docs/snapshots/v0-6-0/latency.mdx`, and the tier section of `docs/releases/v0.6.0.md` |

Two properties of that first publication are stated here rather than only on
the page, because they bound how far the numbers may be read:

- **The gate is the manifest's bound case set.** The site derives its latency
  aggregates at build time from the retained sidecars, and admits a case only
  if `reports/freeze.json` binds that case's result. A sidecar left in the
  tree by a run the freeze does not bind cannot reach a published number.
- **The sidecars are retained beside digest-bound evidence, but `freeze/v1`
  does not itself digest them.** The manifest binds one raw-evidence digest
  per result, and the timing sidecar and the environment stamp are additive
  files beside it. So a latency number in v0.6.0 carries the freeze's
  guarantee that the *run* it belongs to is bound and byte-verified, and only
  the release commit's own immutability for the timing bytes themselves.
  Extending the manifest to bind them is a `freeze/v2` question, deliberately
  not smuggled in under a schema version that does not describe it, and the
  publication says so rather than implying a stronger guarantee than it has.

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
[the challenge tier](challenge-tier.md#amendments), A2–A5, A9, A13, and A16
are in [the modeling matrix](modeling-matrix.md#amendments), A6–A8, A10, A14,
and A17 are in [the tool-native profile](native-profile.md#amendments), and
A11 is in [the adapter contract](adapters.md#amendments). This document joins
that sequence — its first amendment takes the next unused number in the
repository, not A1 — so that an amendment identifier names exactly one
amendment wherever it is cited.

### A12 — 2026-09-01: the four adapters added in v0.6.0 take their granularity rows

**What was preregistered.** The per-adapter granularity table above was
written against the four adapters the benchmark had when this document
merged — CodeQL, Joern, Bifrost, and Semgrep CE — and states that "the
granularity actually achieved per adapter is part of this preregistration".
It named no row for OpenTaint, Infer, FlowDroid, or Pysa, because none of them
existed as an adapter yet.

**Why an amendment and not a silent edit.** Those four adapters landed in the
v0.6.0 cycle (issues #96, #97, #99, #100) and their runners retain timing
sidecars like every other runner. Publishing a latency number for an adapter
whose invocation shape and phase cuts were never declared would be exactly the
after-the-fact decomposition the motivation section above refuses. The table
is immutable from the moment the first latency-bearing artifact was retained,
so the rows are **added by dated amendment, before the first publication of
any number they describe**, rather than backfilled into the original table as
if they had always been there.

**What changes.** Four rows are added to the per-adapter granularity table and
four entries to the cache declarations, each recording the invocation shape
the pinned runner actually uses:

| Adapter | Subprocesses per case | Phases timed |
| --- | --- | --- |
| Infer v1.3.0 | 2 — `infer capture`, then `infer analyze` | `capture`, `analyze` |
| OpenTaint `analyzer/2026.08.27.17eb0fe` | 1 | `total` |
| FlowDroid 2.15.1 | 1 | `total` |
| Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0) | 1 | `total` |

Infer is the second adapter with an observable two-phase shape, and it is the
**same** shape as CodeQL's: a traced compile, then evaluation-and-emission
inside one subprocess. Its `capture` is attributed to capture and never to
analysis, on the same rule that puts CodeQL's traced compiles in `extract`.
The other three expose one subprocess and take one honestly labelled number.

Two costs are named explicitly so that neither is read into a number it is not
in:

- **FlowDroid's per-case APK materialization is excluded.** The released CLI
  analyzes APKs only, so the adapter runs a D8 dex translation and assembles a
  stored-zip APK before spawning the analyzer. That is fixture materialization
  under the exclusion list above, it happens before the timed subprocess is
  spawned, and it is outside every FlowDroid number. A reader comparing
  FlowDroid's total against another adapter's is comparing analyzer
  wall-clock, not the cost of getting a case in front of FlowDroid.
- **Pysa's front-end cost is inside its one number.** The pinned client drives
  the Pyrefly front end and the taint analysis within a single invocation, so
  the front-end/analysis boundary is not adapter-observable and is not guessed
  at. Pysa's `total` is not comparable, phase for phase, with CodeQL's
  `extract` or Infer's `capture`; only whole-invocation totals compare across
  adapters, exactly as corollary 2 above requires.

**A labelling discrepancy, recorded rather than reconciled away.** This
document's CodeQL row names its two phases `extract` and `analyze`. The
instrumentation that landed under issue #90 labels the same two phases
`database-create` and `database-analyze` in the retained sidecars, after the
subcommands that produce them — which is also how this document's own
"subprocesses per case" column already describes them (`database create`, then
`database analyze`). **These are the same two subprocess boundaries with two
spellings; no boundary moved, and nothing is attributed differently.** Because
this document is immutable from the first retained artifact, the row is not
edited to match: the discrepancy is recorded here instead, and publications
use the labels the artifacts actually carry, so a reader can find any
published phase name in the evidence it came from. Infer's row above is
written with the labels its sidecars already use (`capture`, `analyze`), so it
introduces no second instance of this.

**What does not change.** The decomposition rule, the exclusion list, the
environment-scope rule, the aggregation and presentation rules, the non-goals,
and every invariant are untouched, and no existing row is edited: CodeQL's,
Joern's, Bifrost's, and Semgrep's phase cuts are byte-identical to what they
were preregistered as. No phase boundary is moved, and no number that existed
before this amendment is redescribed by it.

**Freezes invalidated.** None. No freeze published a latency number before
this amendment: v0.6.0 is the first, and it is assembled after it.

### A15 — 2026-09-01: warm marginal cost is measured as a separate, labelled figure, and the cold rows stay the headline

> **Amendment number.** This document's amendments continue the repository's
> single sequence. A12 was the sequence's top when this amendment was written
> and it originally claimed A13, but the Infer modeling/native session's
> amendments (A13, A14 — PR #109) merged first, so this amendment was
> renumbered to **A15** at its own merge (PR #111), with every citation moved,
> because an amendment identifier must name exactly one amendment.

**What was preregistered.** "The unit of observation" fixes the unit as the
per-case analyzer invocation and states the consequence in advance: per-case
wall-clock at that granularity "includes per-invocation fixed costs — JVM
start-up, extractor initialization, interpreter start — that a long-lived
deployment of the same engine would amortize", and "the tier does not correct
for this."

That is still the rule, and this amendment does not change it. The cold
per-invocation rows remain exactly what they were, are still the headline
figure, and are not adjusted, corrected, or annotated away by anything below.
Boot is not observable inside one invocation, and a benchmark that spawns one
process per case is right to charge each case for the whole process.

**Why an amendment.** The v0.6.0 publication set eight adapters' cold medians
in one ranked chart, spanning three runtimes: a native binary, a Python CLI,
and five JVM or JVM-fronted engines. A reader comparing those rows across
runtimes reads a start-up difference as a steady-state difference, and the two
are not the same claim. The benchmark is published by the vendor of the engine
that happens to have the smallest start-up cost, which makes the conflation
one this project is least entitled to leave standing.

The honest correction is not to estimate JVM start-up and subtract it — that
would be exactly the after-the-fact adjustment this document's motivation
refuses. It is to **measure the other quantity directly**: run *k* cases
through one tool process, for increasing *k*, and report the slope of batch
wall-clock against *k*. The slope is the cost of one more case in a process
that has already paid its start-up. Start-up is amortized out by construction,
nothing is estimated, and the two figures stand side by side rather than one
replacing the other.

Because that is a measurement this document did not preregister, it is
preregistered here — with its populations, its estimators, its artifacts, and
its declines — **before the first warm number was measured**, on the same terms
every other number in this tier got.

#### What is added

A **warm marginal cost** figure, per adapter and per language, defined as
follows.

- **The measured quantity.** *T(k)*, the wall-clock of one tool process that
  analyzes *k* cases sequentially. The batch sizes are `1, 2, 4, 8, 16` unless
  the adapter's population is smaller, in which case the largest available
  power of two is the top.
- **The unit reported is a slope, never an average.** An average per case at
  *k* still carries a *1/k* share of the fixed cost, which is the very quantity
  the figure exists to remove. Two estimators are published, both of them
  slopes, and neither corrects the other:
  - **endpoint**: `(T(k_max) − T(k_min)) / (k_max − k_min)`;
  - **least squares**: the ordinary-least-squares slope of *T* on *k* over
    every measured point.
  The fit's **intercept** is retained beside them as a descriptive estimate of
  the fixed per-process cost. It is labelled an estimate, and it is never
  subtracted from any measured number.
- **The batched population is a prefix.** Cases are ordered by identifier and
  the *k*-case batch is the first *k* of that list, so every larger batch is a
  strict superset of every smaller one and the difference between two batches
  is attributable to the cases that were added rather than to which cases were
  chosen.
- **The batch does the same work as the cold runs.** The warm runner reuses the
  cold kernel runner's case selection, endpoint resolution, workspace
  materialization, and query logic. For Joern the query block — the frontend
  dispatch, both selectors, and the `reachableByFlows` call — is asserted
  character-for-character identical between `kernel.sc` and the warm batch
  script by a unit test, so the two scripts cannot drift into timing different
  work. `kernel.sc` itself is unmodified; every Joern report's
  `configuration_hash` is a digest over it alone, so no frozen number is
  touched.
- **One clock, at the same kind of boundary.** The only timestamps are the
  runner's monotonic clock around the whole batch subprocess. The warm batch
  script emits no timestamps of its own, and a unit test refuses one that does.
  This document's decomposition rule already excludes "the benchmark's own
  script timestamping itself", and this amendment does not relax it: a warm
  measurement yields one number per batch, not a per-case decomposition.
- **Same environment stamp, same identity witness.** A warm run witnesses the
  pinned binary's version and writes the same `run-environment.json` every
  other run writes. Warm numbers are environment-scoped exactly as cold ones
  are, and are not comparable across machines.
- **Same measurement hygiene.** The standing sequential-run discipline applies
  unchanged — no other analyzer under measurement competes for the machine
  while a batch is timed — and each batch additionally records the machine's
  one-minute load average on the artifact, so the conditions travel with the
  numbers instead of being asserted. A warm run known to have shared the
  machine with another analyzer has unusable timing evidence and is not
  published.
- **A stability check gates publication, and is not itself a statistic.** Each
  measurement is run **twice**, back to back. If the two runs' slopes do not
  agree closely, the figure is **not published**, and the decline is recorded
  in the observability table with both runs retained as its evidence. If they
  do agree, **the second run is the one retained and published** — not an
  average, not a pooled fit, and not whichever of the two reads better. The
  rule names the run by position precisely so that publishing it is not a
  choice. That keeps the non-goal above
  intact: the published figure is a single measurement, and the repeat exists
  only to decide whether it may be published at all. The check is stated on the
  page beside the figure it gates.

#### What is not added

- **No cold number changes.** Not one published median, quartile, minimum or
  maximum is recomputed, adjusted, or re-derived. The cold rows are the
  headline and stay the headline.
- **Warm is never substituted for cold, and never subtracted from it.** They
  are two figures answering two questions: what the benchmark's invocation
  shape costs, and what one more case costs a process already running. A page
  may show both; no page may show a difference of them as though it were a
  measurement.
- **No correctness contact whatsoever.** A warm run writes no normalized
  report, produces no outcome, and touches no scored population. Its artifacts
  land under `reports/raw/warm-latency/`, which the scoring path,
  `validate-reports`, and the freeze manifest never read. Every invariant of
  this document is untouched, including that latency and correctness are never
  pooled.
- **No new statistics.** A slope over five batch sizes, and nothing else. No
  repeated trials, no confidence interval, no steady-state harness — the
  non-goals still hold.
- **No estimated warm figure for an adapter that cannot be measured.** A
  decline is recorded as a decline. Nothing is inferred from an adapter's
  runtime, its published architecture, or another adapter's slope.

#### Per-adapter observability, audited against the released CLI

Each verdict was reached by interrogating the pinned distribution — its help
output, and where the help was ambiguous its own bytecode — never from a
README or an assumption about the runtime. No adapter is patched, forked, or
invoked outside its released interface to make a batch possible; an adapter
that has no batch in what it ships has no warm figure.

| Adapter | Warm marginal observable? | Evidence |
| --- | --- | --- |
| Joern 4.0.614 | **Yes — measured** | `joern --script` runs one Scala script inside one JVM, and a script may import and query any number of case workspaces sequentially. Each case takes its own project name inside the shared workspace, which is the warm process's stand-in for the cold runner's per-case scratch directory: no case can select another's CPG. Verified before any figure was fitted — a two-case batch produced evidence documents whose analyzed state, method counts, endpoint node counts and flow counts match the cold run's retained evidence for the same two cases exactly. |
| Semgrep CE 1.175.0 | **Yes in the released CLI — measured, and the measurement was not stable enough to publish** | `semgrep scan` accepts many target paths in one invocation, so the batch exists and was implemented and run. It accepts one `--config`, so a batch is the same work as its *k* cold runs only when all *k* cases resolve to identical rule text — which caps *k* at 12 here, and every Semgrep kernel in this benchmark invokes exactly 14 cases (the rest being declared-capability `unsupported`, decided before invocation), so no other language raises the ceiling. At that *k* the whole batch runs two to three seconds and the slope is small against the machine's own noise: the same measurement run twice back to back produced slopes differing by roughly a **factor of two**, with one series not even monotone in *k*. Both runs are retained verbatim under `reports/raw/warm-latency/semgrep-java-stability-probe/` as the evidence for this decline. **No Semgrep warm figure is published.** The one thing that survives both runs — that the slope is about an order of magnitude below Semgrep's cold median — is a statement about the shape of the cost and is not published as a number. |
| FlowDroid 2.15.1 | **Yes in the released CLI — not measured here** | `-a/--apkfile` accepts a *directory*: the released `soot-infoflow-cmd` main class lists the directory's APK files, constructs the taint wrapper once outside the loop, and iterates the APKs in one JVM. Its own help text confirms the mode — `-si/--skipapkfile` is documented as "APK file to skip when processing a directory of input files", and the binary refuses a non-directory output with "The output file must be a directory when analyzing multiple APKs". So the batch exists and is observable. It is **not measured under this amendment** because one invocation carries one `-s` sources-and-sinks definition, so a *k*-APK batch runs a union of *k* per-case endpoint configurations rather than each case's own; whether that changes any case's result is an empirical question that must be answered case by case, over the whole population, before a marginal derived from it may be published. Recorded as named follow-up work, not as a decline. |
| OpenTaint `analyzer/2026.08.27.17eb0fe` | **No** | `--project` and `--output-dir` are single-valued and the analyzer exits after one project. A `project.yaml` may list several `javaProjects`, but analyzing that union is one whole-program analysis over a merged call graph with a merged entry-point set — different work, not *k* independent case analyses — and `--semgrep-rule-set` is likewise one rule set for the whole invocation while the benchmark's rules are resolved per case. There is no released mode in which the pinned analyzer processes separate case projects in one process, so the warm marginal is **not observable**, and none is published or estimated. |
| Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0) | **No** | `pyre analyze` is one-shot. The pinned client does expose daemon commands — `start`, `incremental`, `query`, `stop` — but they serve the type checker, not the taint analysis, and `analyze` never attaches to a running server. `--source-directory` is repeatable and merges directories into one project, which is again one whole-program analysis rather than *k*. Each case also carries its own `.pyre_configuration`, its own `pyrefly.toml`, and its own resolved models, which a shared process would have to hold simultaneously. A daemon-shaped measurement would be stateful and not reproducibly preregisterable with this pin, so it is declined rather than attempted. |
| CodeQL 2.26.4 | **No** | `codeql database analyze` takes exactly one mandatory `<database>`, and `database create` produces exactly one database per invocation. Neither subcommand has a multi-database form in the pinned CLI. |
| Infer v1.3.0 | **No** | `--results-dir` names one capture database for one project and the analyzer exits after it. Worth stating rather than leaving implicit: Infer's analyzer is a native binary, and the JVM cost inside its Java row is the traced `javac` in `capture`, which is per-project compilation work, not process start-up that a batch could amortize. |
| Bifrost v0.10.7 | **No — and the decline cannot flatter it** | The policy CLI takes one `--root` per invocation; the repeatable `--workspace NAME=PATH` is documented as requiring `--mcp` and does not reach the policy path. So no warm figure is published for Bifrost. What can be said without measuring anything is a bound, and it is stated so that the missing row is not read as a missing advantage: Bifrost's published cold median already **includes its own process start**, and any warm marginal lies between zero and the cold number it is part of. Adding warm figures can therefore only ever move the *other* rows down toward Bifrost's, never Bifrost's row down further. The asymmetry this amendment corrects is one the publishing vendor's engine loses by, which is the reason to correct it in public. |

#### Where the figures are published, and how they are labelled

- The latency page gains a **separate, explicitly labelled warm-marginal
  section** carrying this table, the measured slopes, the batch series behind
  them, and the declines in the same words they are recorded here.
- Where the ranked chart shows a row that has a warm figure, it may carry a
  **secondary, visually distinguished mark** for the warm marginal beside the
  cold distribution. The cold distribution remains the row's primary and
  determines the ordering. A row without a warm figure carries no mark and the
  page says "not observable with the released CLI" rather than leaving a blank
  that reads as a zero.
- Every warm number is written as what it is: "*X* s marginal per case in a
  warm process, *k* up to *N*", never as a latency, never as *the* number for
  an adapter, and never in the same column as a cold median.

#### Provenance of the warm artifacts

Warm artifacts are retained under `reports/raw/warm-latency/<adapter>-<language>-kernel/`:
the batch series and fitted slopes in `warm-latency.json`, the environment
stamp in `run-environment.json`, and the per-case evidence each batch produced
so that a reader can check the batch did the real work rather than less of it.

They are **auxiliary evidence, outside the freeze**. `freeze/v1` binds
normalized reports and one raw-evidence digest per result; it does not bind
these files, and this amendment does not extend it to — that remains a
`freeze/v2` question, exactly as the timing sidecars' status does under "First
publication" above. A warm figure therefore carries the release commit's
immutability for its bytes and no stronger guarantee, and the publication says
so rather than implying the freeze stands behind it.

**What does not change.** The decomposition rule, the per-adapter granularity
table, the exclusion list, the cache declarations, the environment-scope rule,
the aggregation and presentation rules for the cold tier, the non-goals, and
every invariant. No phase boundary is moved. No number that existed before this
amendment is redescribed by it.

**Freezes invalidated.** None. No cold number changes, no normalized report is
rewritten, and `v0.6.0` is byte-identical before and after this amendment.

### A20 — 2026-09-01: FlowDroid's modeling population declares three subprocess phases

**What changes.** One granularity declaration is **added** for a population
that had no timed artifact before this amendment: the FlowDroid Java
modeling run (`reports/raw/flowdroid-java-modeling/`,
[Amendment A18](modeling-matrix.md#a18--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row)
of the modeling matrix) records three phases per scored case — `compile`
(the two `javac` invocations that materialize the fixture and wrapper
bytecode), `dex` (the D8 translation), and `analyze` (the one FlowDroid
invocation). All three sit at genuinely adapter-observable subprocess
boundaries, so the semi-granular rule is satisfied; nothing is inferred from
inside any tool.

**What does not change, and the comparability rule it forces.** The
FlowDroid *kernel* row above is untouched: its populations keep the single
`analyzer-only` `total`, and no number that existed before this amendment is
redescribed. Only the modeling population's `analyze` phase is an analyzer
number, and it is the phase comparable to the kernels' `total` (both are the
one FlowDroid subprocess, cold JVM start-up included). `compile` and `dex`
are the APK materialization the exclusion rule keeps *out* of analyzer
totals — recorded here as their own labelled phases precisely so they can be
seen without ever being summed into an analyzer's number; a whole-invocation
cross-adapter total for this population is `analyze` alone, per corollary 2.
The tool-native row
([Amendment A19](native-profile.md#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence))
times nothing: its partition hands no case to the analyzer, so it has no
per-case phases at all. Nothing here interacts with
[Amendment A15](#a15--2026-09-01-warm-marginal-cost-is-measured-as-a-separate-labelled-figure-and-the-cold-rows-stay-the-headline)'s
warm-marginal figure: these are cold, per-case, single-process phases.

**Freezes invalidated.** None. The v0.6.0 latency snapshot predates the
population and binds none of its artifacts.

### A21 — 2026-09-01: the warm marginal is published as a range over retained repeats, superseding A15's point figures and its Semgrep withhold

> **Amendment number.** This document's amendments continue the repository's
> single sequence, whose top was A20 when this amendment was written, so it
> claims **A21**. The OpenTaint, FlowDroid and Pysa modeling sessions were
> landing amendments concurrently; if another A21 merges first this one is
> renumbered at its own merge, with every citation moved, because an amendment
> identifier must name exactly one amendment.

**What A15 preregistered, and what it published.**
[A15](#a15--2026-09-01-warm-marginal-cost-is-measured-as-a-separate-labelled-figure-and-the-cold-rows-stay-the-headline)
established the warm-marginal measurement — *k* cases through one tool process,
for increasing *k*, reporting the slope — and gated publication on a **stability
check**: each measurement run twice, the figure withheld if "the two runs'
slopes do not agree closely", and otherwise the second run retained and
published as a point estimate.

Under that rule A15 published one figure and withheld another:

| A15's outcome | What it published |
| --- | --- |
| Joern 4.0.614, Java kernel | **1.55 s** per case (least squares), 1.54 s (endpoint), from a single retained run |
| Semgrep CE 1.175.0, Java kernel | **Withheld.** Two runs' slopes differed by roughly a factor of two, recorded in the observability table as a decline |

**The defect.** The stability rule named no tolerance. "Agree closely" is not a
criterion, and the only moment at which a number could have been chosen for it
was *after* the spreads were known — which is precisely the after-the-fact
decision this document's motivation refuses. The rule therefore did not do the
work it appeared to do: it left the decision to publish or withhold resting on
an unstated judgement, applied once in each direction.

The defect was found the way it should have been: by measuring again. Two
repeats taken on a quiet machine disagreed by 12%, where two taken under load
had agreed to 5%. There was no tolerance that could have been written down at
that point without being fitted to spreads already seen.

**The correction is a rule with no free parameter.** A slope over a handful of
batches on a developer machine has a precision, and there were three ways to
give it one. Publishing a single run to two significant figures hides the
spread and claims more than was measured — that is what A15 did. Gating on an
agreement tolerance requires choosing the tolerance. **Publishing the interval
that was actually measured requires neither.**

So, from this amendment:

- The whole batch series is measured **more than once** — the repeat count is
  fixed in the runner's source, not chosen per run, so a measurement cannot be
  extended until its spread looks narrow.
- **Every repeat is retained**, and what is published is the **range the repeats
  span**, low to high. Its **width is the precision**, visible to the reader
  rather than inferred.
- The repeats are **never averaged** — that would make a repeated trial into a
  statistic, which this tier's non-goals rule out — and **never chosen between**.
- **No figure is withheld or promoted by a threshold.** A wide range is a
  publishable result that reports its own precision, not a disqualification.

Everything else A15 established is untouched and carries forward unchanged: the
slope estimators, the prefix-ordered populations, the same-work requirement, the
single clock at the subprocess boundary, the environment stamp, the
sequential-run hygiene rule, the artifacts' place outside the freeze, and every
rule keeping the warm figure separate from the cold rows. **The cold
per-invocation rows remain the headline and are still neither adjusted nor
subtracted from.**

#### What is superseded

A15's figures are **retired, not edited**. A15 stands as the record of what was
published under the rule it preregistered; the numbers below replace it as the
current figures, re-measured on an idle machine under the range rule.

| Adapter | A15 published | A21 publishes | Cold median, same cases |
| --- | --- | --- | --- |
| Joern 4.0.614, Java | 1.55 s (point) | **996 ms – 1.01 s** | 15.6 s |
| Semgrep CE 1.175.0, Java | *withheld* | **74 – 77 ms** | 1.16 s |

Both A15 artifacts are kept where a reader can find them:
`joern-java-kernel/superseded-a15-warm-latency.json` holds A15's published
Joern figure unedited, beside the live one, and
`reports/raw/warm-latency/README.md` maps the whole directory.

The Joern figure moved by about a third, and the reason is stated rather than
absorbed: **A15's measurement was taken on a busier machine**. Both runs
recorded the one-minute load average before every batch, so this is read off
the artifacts rather than recalled — A15's published run at **9.09 to 9.52** on
a 10-core machine, A21's at **2.02 to 3.92**, in both cases with no competing
analyzer. This document's hygiene rule always required that no other analyzer
compete for the machine, and it was met both times — but "no other *analyzer*"
is a weaker condition than "idle", and the two figures show what the gap
between them is worth. Hence the additional rule below.

- **Observed machine conditions are published beside the figure.** The runner
  already samples the one-minute load average before every batch and retains it;
  from this amendment that sample is **displayed on the page**, as the range
  observed across every batch of every repeat. A reader can then discount a
  figure taken on a busy machine instead of taking the word "quiet" on trust.

#### The Semgrep withhold is reversed, and the misattribution is named

A15 withheld Semgrep's figure because its two runs' slopes differed by a factor
of two, and its observability table recorded that as a property of the
measurement's subject: the batch was too small and the per-case work too slight
for a stable slope. The retained probe README went further and called it an
instability that should not be published.

The retained probe carries the explanation A15 missed, in its own recorded
loads: **probe run 1 ran at load 11.8–11.9 and probe run 2 at load 7.8–8.2**.
Those were not two repeats of one measurement under one condition — the machine
changed underneath them, and the slope moved with it. Re-measured at load
4.1–4.3, **Semgrep's two repeats agree to about 4%**.

The factor-of-two spread was produced by the machine, not by the engine. **The
instability was the measurement's conditions, and attributing it to Semgrep was
a mistake this amendment records rather than quietly drops.**

Two consequences, both deliberate:

- Semgrep's row in the observability table becomes **measured**, on the same
  narrowed population A15 already described: one `--config` per `semgrep scan`
  restricts a batch to cases resolving to identical rule text, so the batched
  population is the largest identical-rule group among the kernel's invocable
  assertions, and the cold median it is compared against is restricted to
  exactly those cases.
- The probe directory A15 cites stays **exactly where A15 put it**, with its
  numbers unedited and a superseding header added. A retracted claim is only
  auditable if it is still legible.

It is worth being plain about the direction of this correction, since this
benchmark is published by the vendor of one of the engines it measures. Both
changes here move numbers **against** that vendor's interest: Joern's marginal
falls by about a third, and a competitor's withheld figure is restored and
turns out to be the *fastest* warm marginal on the page. The rule that produced
them was replaced because it was unsound, not because of which way it pointed.

**What does not change.** The decomposition rule, the per-adapter granularity
table, the exclusion list, the cache declarations, the environment-scope rule,
the cold tier's aggregation and presentation, the non-goals, and every
invariant. No cold number changes. No phase boundary moves. A15's text is
untouched.

**Freezes invalidated.** None. `v0.6.0` is byte-identical before and after this
amendment; warm artifacts are outside the freeze, and no normalized report is
rewritten.
### A24 — 2026-09-01: per-invocation overhead is estimated for every adapter from a trivial no-flow fixture, and labelled an estimate everywhere it appears

> **Amendment number.** This document's amendments continue the repository's
> single sequence. This amendment was drafted as A16 when A15 was the
> sequence's top; the Pysa (A16/A17), FlowDroid (A18–A20), warm-range (A21) and
> OpenTaint (A22/A23) sessions all merged first, so it was renumbered to
> **A24** at its own merge, with every citation in this document, in
> `src/main.rs`, in `docs/src/data/` and in the retained artifacts moved with
> it, because an amendment identifier must name exactly one amendment. A15 and
> A21 carry the same note for the same reason.

**What was preregistered.** A15, as corrected by
[A21](#a21--2026-09-01-the-warm-marginal-is-published-as-a-range-over-retained-repeats-superseding-a15s-point-figures-and-its-semgrep-withhold),
measures a **warm marginal** — the cost of one more case in a process that has
already started — and refuses to estimate one where the released CLI has no
batch: "No estimated warm figure for an adapter that cannot be measured. A
decline is recorded as a decline. Nothing is inferred from an adapter's
runtime, its published architecture, or another adapter's slope." That rule is
unchanged and this amendment does not touch it.

Six of the eight adapters therefore carry **no** figure of any kind for what
their invocation shape charges before analysis begins, while the cold rows
those six are ranked by contain that cost in full. The chart says so in prose;
it shows nothing.

**Why an amendment.** This amendment adds a **different quantity**, measured
rather than inferred, that every adapter can supply: the wall-clock of one
**complete adapter invocation over a trivial no-flow fixture**. It is not a
warm marginal, it is not a substitute for one, and it is never drawn or written
as one. It answers a question the warm marginal cannot: *what does this
adapter's invocation cost before it has anything to find?*

Because it is a new measurement, it is preregistered here — estimator, bias,
fixtures, repeats, artifacts, and presentation — **before the first number was
measured**, on the same terms every other number in this tier got.

#### What is measured

- **The estimator.** For one adapter and one language: materialize a trivial
  no-flow fixture into a scratch workspace, then run **the complete adapter
  invocation** — the same pipeline, the same committed policy, rule, query or
  config path, the same subprocess shape, the same flags, and for a
  two-subprocess adapter both subprocesses — and take the runner's monotonic
  wall-clock around it. For an adapter with declared phases the estimate is the
  sum of its phases, exactly as the cold whole-invocation figure is.
- **The trivial fixture.** One file per language, in the same shape the corpus
  uses: it declares the benchmark's `dfb_source` and `dfb_sink` endpoints, and
  a body that calls the sink on a constant and never connects the two. So the
  endpoint contract resolves, the analysis runs, and there is no flow to find.
  The fixtures are **generated by the runner from templates held in its own
  source**, materialized into scratch, and **retained verbatim beside each
  measurement's artifact**. Nothing is written under `cases/`: no population
  changes, no `case.json` is added, no denominator moves, and the fixture is
  not a case, not scored, and not bound by any freeze.
- **Fixture materialization is outside the timed window**, exactly as it is for
  every cold and warm number: the file is written before the subprocess is
  spawned.

#### What the number is, and what it is biased by

The measurement is **fixed per-invocation overhead plus near-zero analysis**,
so it is an **upper-bound estimate of start-up and warm-up overhead**. It is
labelled an estimate wherever it appears. Both directions of its bias are
stated rather than assumed away:

- **It over-estimates pure boot.** A trivial file is still parsed, still
  extracted, still queried. Whatever that costs is inside the number, so the
  true fixed cost is *at most* the estimate and generally below it. That is why
  the figure is published as an upper bound and never as "the start-up cost".
- **It is a cold, single-shot execution — which is exactly what the cold rows
  contain.** No JIT is warm, no page cache is primed by a previous case of the
  same run. It is therefore the *right* comparator for a cold row and the
  *wrong* one for a steady-state deployment, where both the estimate and the
  cold row would fall. A15's warm marginal remains the only figure this tier
  publishes about steady state.
- **It is one language's number.** An adapter's boot cost is not language-free:
  front ends, extractors and rule sets differ. The estimate is measured in one
  named language per adapter and is labelled with it everywhere.
- **It is not subtracted from anything.** No cold median is corrected by it, no
  difference of it and a cold number is published as a measurement, and it
  never enters an ordering.

#### Range publication, shared with A21

Each measurement is **repeated a fixed number of times**, the count fixed as a
constant in the runner's source rather than chosen per run, **every repeat is
retained**, and **the published figure is the range the repeats span**.

This is the **same convention
[A21](#a21--2026-09-01-the-warm-marginal-is-published-as-a-range-over-retained-repeats-superseding-a15s-point-figures-and-its-semgrep-withhold)
established for the warm marginal**, and it is cited here as shared rather than
re-derived: the argument for it — that publishing a single run to two
significant figures hides the spread, that gating on an agreement tolerance
requires choosing the tolerance, and that publishing the interval actually
measured requires neither — is A21's, and restating it here would let two
statements of one rule drift apart. What this amendment fixes is that the
estimates below are published under it.

Three consequences are load-bearing enough to state:

- **The width of the range is the measurement's precision**, and publishing it
  is publishing that precision. A wide range says the estimate is imprecise,
  which is a thing a reader is entitled to see.
- **Never a mean, and never a chosen repeat.** Not the first, not the last, not
  the median of them, and not whichever reads better.
- **No agreement threshold exists.** There is no tolerance, no
  withhold-on-disagreement rule, and no pass/fail on the repeats agreeing —
  repeats that disagree widen the range, which is the honest consequence of
  disagreeing, rather than triggering a rule that would itself need
  justification and could be tuned. The absence is asserted by a unit test
  against the runner's own source — the same test A21 added for the warm path,
  applied to this one — so a threshold constant cannot creep back in unnoticed.

The earlier draft of this amendment gated publication on two runs agreeing
within `max(20% of the larger, 100 ms)`, on the model of A15's stability check.
**That rule was withdrawn before any estimate was published**, for exactly the
reason A21 gives for withdrawing A15's: a tolerance chosen once the spreads are
known is the after-the-fact decision this document's motivation refuses, and
one chosen before them is a guess that the measurement is then judged against.
No figure was ever published under it. It is recorded here rather than silently
removed, because a rule that was preregistered and then dropped is part of this
amendment's history.

#### Per-adapter fixture language, and the decline vocabulary

Each adapter is measured **in the language of its cheapest kernel arm**: the
core kernel whose published cold whole-invocation median is that adapter's
lowest. A cheap arm is the arm where the fixed cost is the largest share of the
number and therefore where an unstated overhead misleads most; it is also the
arm whose trivial-fixture invocation is least dominated by analysis, which is
the estimator's own bias direction. The rule is fixed in form here; the arm it
selects per adapter is read from the v0.6.0 cold medians.

| Adapter | Fixture language | Why (cold median on that kernel) |
| --- | --- | --- |
| Bifrost v0.10.7 | `python` | 116 ms — its cheapest arm |
| CodeQL 2.26.4 | `ruby` | 4.70 s — its cheapest arm |
| FlowDroid 2.15.1 | `java` | 1.55 s — its cheapest arm |
| Infer v1.3.0 | `c` | 540 ms — its cheapest arm |
| Joern 4.0.614 | `php` | 5.45 s — its cheapest arm |
| OpenTaint `analyzer/2026.08.27.17eb0fe` | `kotlin` | 4.46 s — its cheapest arm |
| Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0) | `python` | 4.08 s — its only arm |
| Semgrep CE 1.175.0 | `kotlin` | 1.09 s — its cheapest arm |

**Joern is additionally measured on `java`**, and both figures are retained.
Java is not its cheapest arm and the java estimate is not the one the
cheapest-arm rule selects; it exists because A15's measured warm marginal and
fitted fixed cost are both java figures, and a three-way comparison between
them and an estimate measured on a different language would be a
cross-population claim. The two Joern estimates are labelled by their own
languages and neither is presented as the other.

There is exactly **one** kind of missing figure, and it is recorded as a
decline rather than a blank. Under the range convention a noisy measurement
produces a wide range rather than no figure, so nothing is ever missing for
having been measured badly:

- **`environment`** — the pinned distribution is not installed in the
  measurement environment, so the invocation could not be attempted at all.
  This is a fact about the machine that ran the estimator, not about the
  adapter's released CLI, and it says nothing about the adapter. It is
  explicitly **not** a capability decline of A15/A21's kind, and it is resolved by
  re-running the estimator where the distribution is installed — the runner
  command and the fixtures are committed so that anyone with the pinned
  distribution can produce the missing row.

Nothing is inferred for a declined adapter. No estimate is derived from a
runtime, an architecture, another adapter's estimate, or another language's
estimate of the same adapter.

#### Measurement hygiene, environment, and artifacts

- **Same discipline, plus a settle step.** The measurements run sequentially on
  a machine checked quiet — no analyzer under measurement competes with
  another — and each invocation records the machine's **one-minute load
  average** immediately before the subprocess is spawned, on the artifact,
  exactly as A21's batches do. Conditions travel with the numbers instead of
  being asserted.

  One addition this measurement needs and A21's did not: nine heavy analyzers
  run back to back **drive the load average up by themselves**, so a run
  started immediately after the previous one records — and is taken under —
  conditions produced by the measurement order rather than by the machine.
  Each adapter's measurement therefore **waits for the load to settle** before
  it begins. The effect is visible in the artifacts of a discarded first
  attempt, where the load climbed from 3.8 on the first adapter to 12.2 by the
  sixth; with the settle step every measurement starts from a comparable idle
  state, and the load each artifact records is a fact about the machine rather
  than about its position in the sequence.
- **Same environment stamp.** Each measurement witnesses the pinned binary's
  version and writes the same `run-environment.json` every other run writes.
  These numbers are environment-scoped and are not comparable across machines.
- **Auxiliary evidence, outside the freeze.** Artifacts are retained under
  `reports/raw/invocation-overhead/<adapter>-<language>/`: every repeat's
  wall-clock, phase split and load average, the retained trivial fixture, the
  resolved configuration where the adapter's is per-case, and the published
  range, in `invocation-overhead.json`, beside the environment stamp. Like
  A15's warm artifacts
  and like the cold timing sidecars, `freeze/v1` does not bind these files;
  they carry the release commit's immutability for their bytes and no stronger
  guarantee, and the publication says so.
- **No correctness contact whatsoever.** The estimator writes no normalized
  report, produces no outcome, reads no case population as a population, and
  touches nothing the scoring path, `validate-reports`, or the freeze manifest
  reads.

#### Where the estimates are published, and how they are drawn

- **The latency page carries the full table**: every one of the eight adapters,
  with its fixture language, every repeat's value, the published range and its
  width, and the range beside that adapter's cold median on the same kernel.
  Every value in the table, published or declined, appears there.
- **The ranked chart draws a mark only above a preregistered significance
  threshold.** A mark at 16 ms on a 123 ms row is clutter, not information: it
  is unreadable at chart scale, and drawing it invites the reading that a mark
  means "slow start-up" when it would mean "a mark was drawn". The threshold is:

  > A row carries an estimate mark when the **low end** of its published range
  > is **at least 25% of that adapter's cold whole-invocation median in the
  > fixture's language**, over that kernel's benchmark-controlled `core`
  > population.

  It is relative rather than absolute because the chart's axis is logarithmic
  and its rows span two orders of magnitude: a share of the row's own median is
  the same visual claim on every row, where a fixed millisecond cut would mark
  every slow adapter and no fast one regardless of what its overhead actually
  is. The 25% cut is the point at which overhead is a *substantial* part of the
  number rather than a rounding contribution to it, and it was written down
  before any estimate existed, so it cannot have been tuned to produce a
  particular set of marks. It reads the range's **low** end so that a mark can
  never appear on the strength of one slow repeat. **Rows below the threshold
  are not blanks**: the chart's caption says marks appear only above it, and
  points at the table, which carries every value.
- **The mark is visually distinct from A15's measured caret**, because the two
  are different quantities and a reader must not read one as the other: the
  measured warm marginal is a **solid caret below the row**, the estimated
  per-invocation overhead is a **dashed span above it**, drawn across the range
  the repeats spanned rather than at a point — a point would claim a precision
  the repeats did not have — and the legend names them in full: "measured warm
  marginal per case" and "estimated per-invocation overhead (trivial fixture,
  upper bound)".
- **Where the mark may be drawn.** In the whole-corpus view, whose row already
  mixes languages and says so, each adapter's mark is its cheapest-arm estimate
  and its language is named in the row's tooltip and in the caption. In a
  per-kernel view, which holds language fixed, a mark appears only if the
  estimate was measured on that same language — an estimate from another
  language is never hung on a language-fixed row. **Joern shows both marks
  where both exist**, and their agreement or disagreement is itself
  informative.
- **Never in the ordering, never subtracted, absent where declined.** Rows are
  ordered by cold median alone, no published number is adjusted by an estimate,
  and a declined adapter carries no mark at all — an absent mark reads as "not
  measured", where a mark at zero would read as "free".

**What does not change.** The decomposition rule, the per-adapter granularity
table, the exclusion list, the cache declarations, the environment-scope rule,
the aggregation and presentation rules for the cold tier, A15's warm-marginal
figure and its declines, the non-goals, and every invariant. No phase boundary
is moved. No cold number is recomputed. No number that existed before this
amendment is redescribed by it.

**Freezes invalidated.** None. No normalized report is rewritten, no case is
added or moved, and `v0.6.0` is byte-identical before and after this amendment.

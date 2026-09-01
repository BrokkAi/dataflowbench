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

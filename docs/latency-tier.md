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
[the challenge tier](challenge-tier.md#amendments), A2–A5 and A9 are in
[the modeling matrix](modeling-matrix.md#amendments), A6–A8 and A10 are in
[the tool-native profile](native-profile.md#amendments), and A11 is in
[the adapter contract](adapters.md#amendments). This document joins
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

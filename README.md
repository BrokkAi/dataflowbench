# DataFlowBench (experimental)

DataFlowBench is an analyzer-neutral benchmark for value flow, taint tracking,
typestate, witness quality, and data-flow performance across languages and
static-analysis tools. It is an experimental first version, not a leaderboard.

The current scored slice has four distinct semantic tracks: `value-flow`,
`taint`, `typestate`, and `performance`. Reports preserve five independent
score dimensions—those tracks plus `witness`—without pooling them. The first
scored slice includes a balanced direct-flow pair across 13 language/dialect
entries and balanced 16-template Java, TypeScript, Python, Kotlin,
C#, Go, and C++ propagation kernels — plus 15-template C and Rust kernels whose
exception-catch cell is inapplicable — in the `taint` track. The Java, Python,
JavaScript, C#, TypeScript, Kotlin, Go, and Scala cores have since expanded to 29
templates each with the
[preregistered challenge tier](docs/challenge-tier.md), the C++ core to 28, the
Rust core to 27 (its reflective-invocation cell is inapplicable too), and the C
core to 24 (nine of the thirteen challenge templates are applicable to C); the
16-template, 24-template, 27-template, 28-template, and
29-template populations are separate populations of the same name. Each parity kernel uses the
same language-neutral template IDs with language-specific fixture spellings and
a separate result population; the [Python kernel
contract](docs/python-kernel.md), the [TypeScript adaptation
matrix](docs/typescript-kernel.md), the [Kotlin kernel
contract](docs/kotlin-kernel.md), the [C# kernel
contract](docs/csharp-kernel.md), the [Go kernel
contract](docs/go-kernel.md), the [C](docs/c-kernel.md) and
[C++](docs/cpp-kernel.md) kernel contracts, and the [Rust kernel
contract](docs/rust-kernel.md) record those adaptations. DataFlowBench measures correctness, capability coverage, witness
quality, and performance separately; it deliberately does not calculate a
combined score or declare a tool a winner.

## What it measures—and does not

Cases state source-to-sink flows, expected nonflows, capability requirements,
bounded witnesses, and execution budgets. Reports preserve the outcome and
evidence for one exact tool configuration. This does not measure complete
whole-program soundness, general path feasibility, every language feature, or
real-project accuracy. Unsupported and inconclusive outcomes are kept separate
from `not-reached`, so a tool is never penalized outside its documented scope.

Scored cases are balanced semantic pairs: every language-neutral `core`
template has one positive and one minimally different negative for each
language and model profile. The bootstrap fixtures are calibration cases and do
not yet constitute a score. See the [scoring contract](docs/scoring.md).

External tools are compared respectfully: publish their exact version, settings,
supported dimensions, normalized outcomes, and raw evidence. Semgrep CE stays
in its supported local-analysis profile; OpenTaint stays in its Java/Kotlin
profile. SootUp is a possible JVM reference framework, not a first-version
adapter. CodeQL is implemented for all ten propagation kernels, one language-scoped
command and one separate result population per language. Joern is implemented
for the Java, JavaScript, Python, Ruby, PHP, and Rust propagation kernels on the
same terms.
Semgrep CE is implemented for eleven languages as a deliberately bounded
adapter: only the intraprocedural partition its pinned distribution documents
the open-source taint engine as covering is scored, and the interprocedural and
heap templates are `unsupported` by a capability decision taken from the case
metadata before Semgrep is ever invoked. Four of its front ends are not GA in
that distribution — Kotlin `beta`, Rust/C/C++ `alpha` — and the label is
retained on every assertion without ever changing the partition. Scala is left
recorded-only by maintainer decision rather than by any tool limitation; C# is
Pro-only and cannot be run on CE at all.

## Quick start

```bash
cargo fmt --check
cargo test
cargo run -- validate
python3 scripts/validate-python-kernel.py
cargo run -- validate-reports
cargo run -- run-bifrost-smoke --bifrost /path/to/current-bifrost
cargo run -- run-bifrost-javascript-kernel --bifrost /path/to/current-bifrost
cargo run -- run-codeql-java-kernel --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
cargo run -- run-codeql-python-kernel --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
cargo run -- run-bifrost-typescript-kernel --bifrost /path/to/current-bifrost
cargo run -- run-codeql-typescript-kernel --codeql /path/to/codeql
cargo run -- run-bifrost-csharp-kernel --bifrost /path/to/current-bifrost
cargo run -- run-codeql-csharp-kernel --codeql /path/to/codeql
cargo run -- run-bifrost-go-kernel --bifrost /path/to/current-bifrost
cargo run -- run-codeql-go-kernel --codeql /path/to/codeql --go /path/to/go
cargo run -- run-bifrost-c-kernel --bifrost /path/to/current-bifrost
cargo run -- run-bifrost-cpp-kernel --bifrost /path/to/current-bifrost
cargo run -- run-codeql-c-kernel --codeql /path/to/codeql
cargo run -- run-codeql-cpp-kernel --codeql /path/to/codeql
cargo run -- run-bifrost-rust-kernel --bifrost /path/to/current-bifrost
cargo run -- run-codeql-rust-kernel --codeql /path/to/codeql
cargo run -- run-joern-java-kernel --joern /path/to/joern
cargo run -- run-joern-javascript-kernel --joern /path/to/joern
cargo run -- run-joern-python-kernel --joern /path/to/joern
cargo run -- run-joern-ruby-kernel --joern /path/to/joern
cargo run -- run-joern-php-kernel --joern /path/to/joern
cargo run -- run-joern-rust-kernel --joern /path/to/joern
cargo run -- run-semgrep-java-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-javascript-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-typescript-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-python-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-go-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-ruby-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-php-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-kotlin-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-rust-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-c-kernel --semgrep /path/to/semgrep
cargo run -- run-semgrep-cpp-kernel --semgrep /path/to/semgrep
```

The Bifrost smoke command requires a current Bifrost build with policy CLI
support (the checked-out sibling repository is suitable) and executes
Bifrost's real policy CLI against the selected positive and negative fixtures,
including the Java and JavaScript kernels. It retains raw JSON in
`reports/raw/bifrost/` and writes `reports/bifrost-smoke.json`. Bifrost returns
exit status 1 for a finding; the runner treats that as successful evidence
rather than a runner failure. The CodeQL commands require a CodeQL CLI and the
corresponding pinned language pack: the Java command runs only the Java kernel,
while the Python command selects exactly the Python core assertions — 58 now
that its challenge-tier row is rolled out — and runs the Python-specific query.

The Java and Python CodeQL query packs are separate. Install the Java pack from
`adapters/codeql/` for the Java command and the Python pack from
`adapters/codeql/python/` for the Python command; each pack resolves its own
language-specific database-schema dependency.

The Python CodeQL command writes `reports/codeql-python-kernel.json` and keeps
one raw SARIF or runner-error artifact per selected case under
`reports/raw/codeql-python-kernel/`. It preserves source/sink anchor metadata and the
five outcomes `reached`, `not-reached`, `inconclusive`, `unsupported`, and
`runner-error`; incomplete or failed analysis is never normalized as a
negative. The validated Python run used CodeQL CLI 2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/python-all@7.2.3`. Its 32 results are 14 `reached` and 18
`not-reached`, with no `inconclusive`, `unsupported`, or `runner-error`
outcomes; 28/32 match the expected polarity. The mismatches are false
negatives for `alias-propagation-positive`, `array-element-positive`, and
`exception-catch-positive`, plus a false positive for `loop-carried-negative`.
This evidence is limited to the Python core kernel.

The six Joern commands require a Joern installation and — for PHP only — a host
`php` interpreter; every case is a single checked-in source file with no
compilation step. They write `reports/joern-<language>-kernel.json` and keep one
raw evidence document per case under `reports/raw/joern-<language>-kernel/`. The
retained snapshot used Joern 4.0.610 with the `javasrc2cpg`, `jssrc2cpg`,
`pysrc2cpg`, `rubysrc2cpg`, `php2cpg`, and `rust2cpg` frontends and one committed
CPG query script. All 344 assertions executed with no `inconclusive`,
`unsupported`, or `runner-error` outcome: Java 47/58, JavaScript 44/58, Python
48/58, PHP 48/58, Ruby 40/58, and Rust 43/54 match the expected polarity —
Rust's denominator is the expanded 27 templates, two cells being inapplicable to
it, and Java's, Python's, JavaScript's, PHP's, and Ruby's are the expanded 29
each, whose 58-assertion populations are never compared to a 32-assertion one.
JavaScript splits 26/32 on the classic sixteen — identical to its earlier
snapshot — and 18/26 on the challenge thirteen, Java splits 28/32 and 19/26 the
same way, Python splits 28/32 and 20/26, PHP splits 28/32 and 20/26, Ruby splits
26/32 and 14/26, and Rust splits 27/30 and 16/24, each classic half identical
case for case to its pre-expansion snapshot. In Java, JavaScript, Python, PHP,
and Rust the depth-6 relay positive is missed at the distribution's default
call-depth bound of 4, exactly as the challenge preregistration predicted in
advance. Ruby is the one measured departure: on the same pin and the same
default bound it discriminates the depth-6 relay pair correctly, and that result
is recorded as measured rather than smoothed toward the prediction. Rust's
challenge stratum is the
first challenge-tier engine evidence here for a systems language, and it is
uniformly under-approximating: every stratum-A and stratum-B negative correct,
every stratum-A and stratum-B positive missed, and not one false positive in the
twelve challenge templates. Rust became runnable only at this pin:
`rust2cpg` is new in 4.0.610, it needs a Cargo manifest the runner synthesizes
per workspace, and it is recorded as the young frontend it is. Scala still has
no source frontend and stays explicitly unsupported. Re-running all six on the
new pin left Java, JavaScript, Python, and PHP identical case-for-case and moved
four Ruby cases in opposite directions at an unchanged 26/32 on the classic
sixteen. See the
[Joern adapter evidence](adapters/joern/README.md) for the pinned invocation,
tagging model, frontend coverage, drift analysis, and per-language mismatch
lists.

The eleven Semgrep commands require only a Semgrep CE installation — no
compiler, no JVM, no `Cargo.toml`, not even for the C, C++, Rust, and Kotlin
kernels. They write `reports/semgrep-<language>-kernel.json` and keep, per case,
either the native `--json` finding document plus the exact resolved rule it was
analyzed under, or a capability-decision document for a case outside the scored
profile. The retained snapshot used Semgrep CE 1.174.0 (Homebrew) with
`--oss-only` and `--metrics=off` on every scan. Only the 14-assertion
intraprocedural partition of each kernel is scored — the pinned CLI documents
interprocedural taint, cross-file taint, and path sensitivity as Pro Engine
features, so the rest is `unsupported` rather than false negatives. All eleven
kernels produced 9 `reached`, 5 `not-reached`, and the whole remainder
`unsupported` — every kernel is now expanded, so the remainder is 34 for the
expanded 24-template C kernel, 40 for the expanded 27-template Rust kernel, 42
for the expanded 28-template C++ kernel, and 44 each for the expanded
29-template Java, Python, JavaScript, TypeScript, Kotlin, Go, PHP, and Ruby
kernels, 468 preregistered-unsupported assertions against 154 scored across
622 selected cases — with no `inconclusive` or `runner-error`
outcome and 12/14 of each scored subset matching the expected polarity; every
intraprocedural positive was found in every language. The two mismatches are the
same in all eleven — false positives on the infeasible branch and the
loop-carried kill, exactly the path sensitivity the pinned CLI sells as Pro. The
four non-GA front ends score identically to the seven GA ones on this narrow
partition, which is a result about local propagation and not a general claim
about those parsers. See the
[Semgrep adapter evidence](adapters/semgrep/README.md) for the pinned version,
the documented-scope and maturity citations, and the per-language partition.

The checked-in Bifrost v0.10.5 snapshot contains 118 normalized results:
58 `reached`, 57 `not-reached`, 2 `inconclusive`, and 1 `unsupported`. It was
produced from build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`.
The Java, Python, and JavaScript 32-assertion kernels each have 32/32
expected-polarity matches with no decisive mismatches and no incomplete
outcomes; under v0.10.2 they stood at 17/32, 16/32, and 19/32. Those are the
frozen v0.3.0 16-template populations. Python's core has since expanded to 29
templates and 58 assertions, and its Bifrost evidence for that larger
population is deferred to the v0.4.0 freeze-prep re-run rather than being
published here — the frozen report may not be overwritten; Java and JavaScript
publish theirs through their own dedicated kernel commands, below. Incomplete
outcomes remain distinct from decisive semantic mismatches and are never
treated as negative results.

JavaScript has since been expanded by the thirteen preregistered challenge
templates to a 29-template, 58-assertion core, run by the dedicated
`run-bifrost-javascript-kernel` command into
`reports/bifrost-javascript-kernel.json` — the frozen smoke report is untouched
and its population is still pinned at 118 cases. That run reproduces 32/32 on
the classic half and decides only three of the 26 challenge assertions, all
three correctly; the other 23 are `inconclusive` or `runner-error` and are
counted as neither positives nor negatives. A 32-assertion score and a
58-assertion score are different populations and are never compared as one. See
the [Bifrost adapter evidence](adapters/bifrost/README.md)
and the [JavaScript adaptation matrix](docs/javascript-kernel.md) for the
per-slice breakdown and retained raw-report contract.

Java has been expanded the same way, run by the dedicated
`run-bifrost-java-kernel` command into `reports/bifrost-java-kernel.json` — the
first evidence that command has produced, and again with the frozen smoke report
untouched at its pinned 118 cases. That run also reproduces **32/32 on the
classic half, case for case with the frozen smoke slice**, and decides five of
the 26 challenge assertions, all five correctly; the other 21 are 19
`inconclusive` and 2 `runner-error` on the `element-object` cell
(`internal_invariant`), counted as neither positives nor negatives. See the
[Java kernel contract](docs/java-kernel.md) for the per-slice breakdown.

TypeScript has since been expanded the same way, to a 29-template,
58-assertion core. It is the one wave so far with **no** expanded analyzer
outcomes at all: its Bifrost *and* CodeQL reports are both freeze-bound by
v0.3.0, so both runs are deferred to the v0.4.0 freeze-prep re-run, and Joern
has no TypeScript slice to run. Only Semgrep CE covered the expanded
population, and it declines all 26 challenge assertions by declared capability.
The [TypeScript adaptation matrix](docs/typescript-kernel.md) records the
deferral and what it does and does not leave established.

Go has since been expanded the same way, to a 29-template, 58-assertion core,
with three cells language-adapted through the `reflect` package and the
`HandlerFunc` idiom exactly as the preregistration prescribes. It is in the same
position as TypeScript: its Bifrost *and* CodeQL reports are both freeze-bound
by v0.3.0, so both runs are deferred to the v0.4.0 freeze-prep re-run, and the
Joern adapter has no Go slice to run. Only Semgrep CE covered the expanded
population, and it declines all 26 challenge assertions by declared capability.
The [Go kernel contract](docs/go-kernel.md) records the deferral and what it
does and does not leave established.

C carries the most sharply **reduced** challenge denominator so far: four of
the thirteen templates are inapplicable to a language with no reflection, no
computed member access, no closures, and no anonymous types, so its core is 24
templates / 48 assertions rather than 29 / 58. Its Bifrost and CodeQL reports
are both freeze-bound by v0.3.0 and both re-runs are deferred to v0.4.0, Joern
has no C slice, and Semgrep CE declines all 18 challenge assertions by declared
capability. The [C kernel contract](docs/c-kernel.md) records the four
exclusions, the four adapted cells, and the deferral.

Scala has since been expanded the same way, to a 29-template, 58-assertion core,
with the two reflection cells language-adapted through `java.lang.reflect`
because `scala-reflect` is a separate artifact the stdlib-only rule excludes. It
is the inverse of the TypeScript and Go position: Scala has **single-analyzer
coverage** — no CodeQL extractor, no Joern Scala source frontend, and no
commissioned Semgrep slice — but its one covering adapter's report is *not*
freeze-bound, so `run-bifrost-scala-kernel` was re-run whole over all 58 and
nothing is deferred. That run reproduces the classic 32 case for case at 10/32
and leaves **all 26 challenge assertions `inconclusive`** — capability coverage
that is neither 26 matches nor 26 misses. The [Scala kernel
contract](docs/scala-kernel.md) records the adaptations and the per-stratum
evidence.

PHP has since been expanded the same way, to a 29-template, 58-assertion core
with **all thirteen cells directly applicable** — variable method calls,
variable property access, arrays of closures, `use`-clause closures,
closure-valued properties, and genuine anonymous classes. Like Scala it defers
**nothing** — but unlike Scala it is covered by more than one adapter: no PHP
report is freeze-bound, so all three of its
adapters ran the whole expanded population. Bifrost reproduces its classic
17/32 exactly and decides 4 of the 26 challenge assertions, all correctly,
declining the other 22; Joern executes every case and scores 48/58 (28/32
classic, 20/26 challenge, with stratum C answered completely); Semgrep CE
declines all 26 challenge assertions by declared capability. PHP has no CodeQL
extractor at all, which is an absence of an analyzer rather than a deferral.
The [PHP kernel contract](docs/php-kernel.md) records the fixtures, the
per-stratum results, and the mismatch lists.

Ruby is the last of the thirteen, expanded to a 29-template, 58-assertion core
with **all thirteen cells directly applicable**, and it defers nothing at all:
Ruby's kernel landed after the v0.3.0 freeze, so none of its four reports is
freeze-bound and **all four adapters ran the whole expanded population** — the
only language for which that is true. `reports/codeql-ruby-kernel.json` is
consequently the only CodeQL report in this repository that reflects the
challenge tier, scoring 49/58 (29/32 classic, 20/26 challenge) with a clean 6/6
on stratum D. Joern scores 40/58 (26/32 and 14/26) and supplies the wave's one
**recorded measured departure**: at the same unraised `maxCallDepth = 4` that
makes Java, JavaScript, Python, PHP, and Rust miss the depth-6 relay positive,
Ruby discriminates that pair correctly — reported as measured rather than
reconciled to the preregistered prediction, which stands unamended. Semgrep CE
scores 12/14 on its intraprocedural partition and declines the other 44
assertions by declared capability; Bifrost returns all 58 `inconclusive`, 14 of
them under a new *taint semantic binding is unavailable* diagnostic class, which
is recorded absence of capability rather than 58 negatives. The [Ruby kernel
contract](docs/ruby-kernel.md) records the fixtures, the per-stratum results,
and the mismatch lists.

**With Ruby's row flipped the challenge-tier rollout is complete: all thirteen
core kernels carry their preregistered expanded denominators**, and what remains
outstanding is adapter re-runs the v0.3.0 freeze defers to v0.4.0, not missing
fixtures.

## Add a case or adapter

Copy the shape in `cases/taint/java/`, keep marker anchors stable, and validate
the case. The schema is versioned and deliberately analyzer-neutral. A `core`
case will not validate until its opposite-polarity partner exists. Read the
[fixture provenance rules](docs/fixture-provenance.md), then put a native rule
or model in `adapters/<tool>/`; add a command and normalization mapping in the
[adapter contract](docs/adapters.md) before publishing a result.

Reproduce a checked-in example with `cargo run -- validate-reports`; recreate a
fresh Bifrost report with the quick-start command and compare its raw evidence.
The Python kernel check enforces the exact 29-template positive/negative
population independently of any analyzer output.
The [CodeQL adapter guide](adapters/codeql/README.md) documents the pinned CLI,
language packs, and commands for reproducing retained kernel reports, and the
[Joern adapter guide](adapters/joern/README.md) does the same for the pinned
Joern distribution, its query script, and its frontend coverage. The
[Semgrep adapter guide](adapters/semgrep/README.md) does the same for the pinned
Semgrep CE distribution, its committed taint rules, and the bounded profile it
scores. The
[Python kernel contract](docs/python-kernel.md) defines the exact 29-template,
58-assertion selection, the challenge-tier expansion behind it, and its
anchor-based result semantics. The [C# kernel
contract](docs/csharp-kernel.md), the [Go kernel
contract](docs/go-kernel.md), the [C](docs/c-kernel.md) and
[C++](docs/cpp-kernel.md) kernel contracts, and the [Rust kernel
contract](docs/rust-kernel.md) do the same for C#, Go, C, C++, and Rust; all
of that evidence is frozen in the published v0.3.0 release.

The [taint-modeling matrix](docs/modeling-matrix.md) is a separate tier that
asks a separate question: not whether an engine can follow flow it can see, but
whether it can be **told** things. Each language row is twenty-four
benchmark-controlled modeling assertions, four per-adapter model encodings, and
one run per adapter against them. Wave M1's three rows are complete:
[the Python taint-modeling matrix](docs/python-modeling.md),
[the JavaScript taint-modeling matrix](docs/javascript-modeling.md), and
[the Java taint-modeling matrix](docs/java-modeling.md). Modeling
cases are `score_tier: "modeling"`, are never in a core denominator, and are
never averaged with a kernel score.

The [tool-native profile](docs/native-profile.md) inverts that question once
more: not what an engine does with models we supply, but what each vendor's
**shipped product** covers over code that calls real platform APIs. It shares
the `modeling` tier and is separated from the matrix by `model_profile` alone,
and the two are never pooled — a native miss is a coverage fact about a
catalog, not an accuracy fact about an engine. Wave N1's first row is
[the Java tool-native probe set](docs/java-native.md): six templates, twelve
assertions, and no benchmark-authored model of any kind.

The [Java kernel contract](docs/java-kernel.md) records the origin population
and the first landed wave of the [challenge-tier
expansion](docs/challenge-tier.md), which grows the Java core to 29 templates
and 58 assertions. That expanded population is unreleased and is a different
population from the v0.3.0 core; the two are never compared number to number.

## Licenses and provenance

Code, schemas, adapters, tools, and authored fixtures are [MIT](LICENSE).
Annotations, ground truth, measurements, and generated benchmark data are
[CC0-1.0](LICENSE-DATA). Imported projects remain under their original licenses;
their origin, pinned revision, and license must be recorded in the case
provenance. The initial fixtures are authored in this repository.

## Roadmap

The [milestone plan](docs/milestones.md) starts with a one-template breadth
baseline across Bifrost's supported languages, deepens that into balanced
16-template Java, JavaScript, and Python propagation kernels, then expands
cross-language parity and adds separately scored taint-modeling and real-project
slices. All three kernels preserve the same semantic IDs with balanced
positive/negative cases and separate retained evidence. The
[benchmark-source inventory](docs/benchmark-sources.md) records suites used as
design inputs. A large real-project corpus, a custom query language, a general
framework, a typestate solver, and a combined leaderboard are intentionally out
of scope.

## Freeze release evidence

Before using benchmark results in a release or website claim, create an
immutable `freeze/v1` manifest and validate it from a clean checkout:

```bash
cargo run -- validate-freeze reports/freeze.json
```

The [freeze contract](docs/freeze.md) explains the bound benchmark revision,
case and fixture digests, adapter identities, normalized reports, retained raw
evidence, claim partitions, exclusions, and the rule that corrected results
create a new freeze instead of rewriting an old one.

Publishable result pages are then generated — never hand-written — from the
validated freeze:

```bash
cargo run -- generate-results --manifest reports/freeze.json --output-directory site/results
```

The [result generation contract](docs/results.md) describes the byte-stable
JSON and Markdown artifacts, their scorecard partitions, and the `--check`
mode that proves checked-in artifacts match the freeze they cite.

## Website

The public site at <https://brokkai.github.io/dataflowbench> is an Astro
Starlight package in `docs/`; every number it shows is rendered from the
generated `results/results.json`, never hand-authored. Develop locally with:

```bash
npm --prefix docs install
npm --prefix docs run dev
```

CI runs `npm ci`, `npm run check`, and `npm run build`; deployment to GitHub
Pages is manual via the “Deploy site” workflow.

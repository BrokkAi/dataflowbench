# DataFlowBench (experimental)

DataFlowBench is an analyzer-neutral benchmark for value flow, taint tracking,
typestate, witness quality, and data-flow performance across languages and
static-analysis tools. It is an experimental first version, not a leaderboard.

It has four distinct tracks: `value-flow`, `taint`, `typestate`, and
`performance`. The first scored slice includes a balanced direct-flow pair
across 13 language/dialect entries and balanced 16-template Java, JavaScript,
and Python propagation kernels in the `taint` track. Python parity uses the
same language-neutral template IDs with Python-specific fixture spellings and
a separate result population; the [Python kernel contract](docs/python-kernel.md)
records those adaptations. DataFlowBench measures correctness, capability
coverage, witness quality, and performance separately; it deliberately does
not calculate a combined score or declare a tool a winner.

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
adapter. CodeQL is implemented for the full Java propagation kernel.

## Quick start

```bash
cargo fmt --check
cargo test
cargo run -- validate
python3 scripts/validate-python-kernel.py
cargo run -- validate-reports
cargo run -- run-bifrost-smoke --bifrost /path/to/current-bifrost
cargo run -- run-codeql-java-kernel --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The Bifrost smoke command requires a current Bifrost build with policy CLI
support (the checked-out sibling repository is suitable) and executes
Bifrost's real policy CLI against the selected positive and negative fixtures,
including the Java and JavaScript kernels. It retains raw JSON in
`reports/raw/bifrost/` and writes `reports/bifrost-smoke.json`. Bifrost returns
exit status 1 for a finding; the runner treats that as successful evidence
rather than a runner failure. The separate CodeQL command requires a CodeQL
CLI and Java pack checkout and runs the pinned Java-kernel adapter.

The checked-in Bifrost snapshot contains 88 normalized results: 39 `reached`,
42 `not-reached`, 6 `inconclusive`, and 1 `unsupported`, from Bifrost 0.9.5
build `0b0c5c0e2d84eb7fc75baa486f6111623b13507c`. All 32 Java-kernel
assertions match their expected polarity. The 32 JavaScript-kernel assertions
have 22 matching complete outcomes, 6 complete polarity mismatches, and 4
`inconclusive` outcomes; the latter are incomplete analysis and are never
translated into negative results. See the [Bifrost adapter evidence](adapters/bifrost/README.md)
and the [JavaScript adaptation matrix](docs/javascript-kernel.md) for the
per-slice breakdown and retained raw-report contract.

## Add a case or adapter

Copy the shape in `cases/taint/java/`, keep marker anchors stable, and validate
the case. The schema is versioned and deliberately analyzer-neutral. A `core`
case will not validate until its opposite-polarity partner exists. Read the
[fixture provenance rules](docs/fixture-provenance.md), then put a native rule
or model in `adapters/<tool>/`; add a command and normalization mapping in the
[adapter contract](docs/adapters.md) before publishing a result.

Reproduce a checked-in example with `cargo run -- validate-reports`; recreate a
fresh Bifrost report with the quick-start command and compare its raw evidence.
The Python kernel check enforces the exact 16-template positive/negative
population independently of any analyzer output.
The [CodeQL adapter guide](adapters/codeql/README.md) documents the pinned CLI,
Java pack, and command for reproducing its retained kernel report.

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

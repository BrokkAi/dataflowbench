# DataFlowBench (experimental)

DataFlowBench is an analyzer-neutral benchmark for value flow, taint tracking,
typestate, witness quality, and data-flow performance across languages and
static-analysis tools. It is an experimental first version, not a leaderboard.

It has four distinct tracks: `value-flow`, `taint`, `typestate`, and
`performance`. The first executable slice is the Java `taint` track. It
measures correctness, capability coverage, witness quality, and performance
separately; it deliberately does not calculate a combined score or declare a
tool a winner.

## What it measures—and does not

Cases state source-to-sink flows, expected nonflows, capability requirements,
bounded witnesses, and execution budgets. Reports preserve the outcome and
evidence for one exact tool configuration. This does not measure complete
whole-program soundness, general path feasibility, every language feature, or
real-project accuracy. Unsupported and inconclusive outcomes are kept separate
from `not-reached`, so a tool is never penalized outside its documented scope.

External tools are compared respectfully: publish their exact version, settings,
supported dimensions, normalized outcomes, and raw evidence. Semgrep CE stays
in its supported local-analysis profile; OpenTaint stays in its Java/Kotlin
profile. SootUp is a possible JVM reference framework, not a first-version
adapter.

## Quick start

```bash
cargo fmt --check
cargo test
cargo run -- validate
cargo run -- validate-reports
cargo run -- run-bifrost-smoke --bifrost /path/to/current-bifrost
```

The last command requires a current Bifrost build with policy CLI support (the
checked-out sibling repository is suitable) and executes Bifrost's real policy CLI against the positive and
sanitized fixtures, retains raw JSON in `reports/raw/bifrost/`, and writes
`reports/bifrost-smoke.json`. Bifrost returns exit status 1 for a finding; the
runner treats that as successful evidence rather than a runner failure.

## Add a case or adapter

Copy the shape in `cases/taint/java/`, keep marker anchors stable, and validate
the case. The schema is versioned and deliberately analyzer-neutral. Read the
[fixture provenance rules](docs/fixture-provenance.md), then put a native rule
or model in `adapters/<tool>/`; add a command and normalization mapping in the
[adapter contract](docs/adapters.md) before publishing a result.

Reproduce a checked-in example with `cargo run -- validate-reports`; recreate a
fresh Bifrost report with the quick-start command and compare its raw evidence.

## Licenses and provenance

Code, schemas, adapters, tools, and authored fixtures are [MIT](LICENSE).
Annotations, ground truth, measurements, and generated benchmark data are
[CC0-1.0](LICENSE-DATA). Imported projects remain under their original licenses;
their origin, pinned revision, and license must be recorded in the case
provenance. The initial fixtures are authored in this repository.

## Roadmap

The next slices add value-flow, typestate, and performance cases; Bifrost,
CodeQL, Semgrep CE, and OpenTaint adapters; cross-language fixtures; witness
quality checks; and reproducible performance environments. A large real-project
corpus, a custom query language, a general framework, a typestate solver, and a
combined leaderboard are intentionally out of scope.

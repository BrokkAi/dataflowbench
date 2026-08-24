# DataFlowBench (experimental)

DataFlowBench is an analyzer-neutral benchmark for value flow, taint tracking,
typestate, witness quality, and data-flow performance across languages and
static-analysis tools. It is an experimental first version, not a leaderboard.

The current scored slice has four distinct semantic tracks: `value-flow`,
`taint`, `typestate`, and `performance`. Reports preserve five independent
score dimensions—those tracks plus `witness`—without pooling them. The first
scored slice includes a balanced direct-flow pair across 13 language/dialect
entries and balanced 16-template Java, JavaScript, and Python propagation
kernels in the `taint` track. Python parity uses the same language-neutral
template IDs with Python-specific fixture spellings and a separate result
population; the [Python kernel contract](docs/python-kernel.md) records those
adaptations. DataFlowBench measures correctness, capability coverage, witness
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
adapter. CodeQL is implemented for the Java propagation kernel and has a
language-scoped Python command for the separate 32-assertion Python kernel.

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
cargo run -- run-codeql-python-kernel --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The Bifrost smoke command requires a current Bifrost build with policy CLI
support (the checked-out sibling repository is suitable) and executes
Bifrost's real policy CLI against the selected positive and negative fixtures,
including the Java and JavaScript kernels. It retains raw JSON in
`reports/raw/bifrost/` and writes `reports/bifrost-smoke.json`. Bifrost returns
exit status 1 for a finding; the runner treats that as successful evidence
rather than a runner failure. The CodeQL commands require a CodeQL CLI and the
corresponding pinned language pack: the Java command runs only the Java kernel,
while the Python command selects exactly the 32 Python core assertions and
runs the Python-specific query.

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

The checked-in Bifrost v0.10.2 snapshot contains 118 normalized results:
50 `reached`, 37 `not-reached`, 30 `inconclusive`, and 1 `unsupported`. It was
produced from build identity
`c2116609f5fc1be318c8fb76fb83763cf326bab6`, whose Bifrost binary SHA-256 is
`93b55dd20c283c278f586e8c8e6ad6bf0e9f5f08165b56096e110af0450d0873`.
The Java, Python, and JavaScript 32-assertion kernels have respectively 17/32
expected-polarity matches, 5 decisive mismatches, and 10 incomplete
`inconclusive` outcomes; 16/32, 4 decisive mismatches, and 12 incomplete
`inconclusive` outcomes; and 19/32, 7 decisive mismatches, and 6 incomplete
`inconclusive` outcomes. Incomplete outcomes remain distinct from decisive
semantic mismatches and are never treated as negative results. This v0.10.2
evidence matches the retained v0.10.1 outcomes case-for-case, and does not
restore the complete Java correctness observed in the v0.9.5 snapshot. See the [Bifrost adapter evidence](adapters/bifrost/README.md)
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
language packs, and commands for reproducing retained kernel reports. The
[Python kernel contract](docs/python-kernel.md) defines the exact 16-template,
32-assertion selection and its anchor-based result semantics. The [C# kernel
contract](docs/csharp-kernel.md) does the same for C#; its evidence postdates
the v0.2.0 freeze and is not part of the published release numbers above.

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

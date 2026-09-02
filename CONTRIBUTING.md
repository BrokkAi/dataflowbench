# Contributing

DataFlowBench is experimental. Keep each change small, reproducible, and clear
about what it establishes.

## Cases

Add a case directory beneath `cases/<track>/<language>/`. A case must validate
against `schemas/case.schema.json`, use stable `DFB-*` source and sink markers,
and include fixture provenance. Authored fixtures use MIT; imported fixtures
keep their original license and must record origin, revision, and license.

The canonical case describes flows and nonflows without naming an analyzer.
Native rules, models, commands, and documented limitations belong under that
tool's `adapters/` directory. Do not turn unsupported or inconclusive execution
into a `not-reached` result.

Every `core` semantic template requires exactly one positive and one negative
case for the same track, language, and model profile. Give negatives an explicit
mechanism; do not satisfy the balance contract with a large class of trivial
safe literals. Use `calibration` while adapter plumbing or a pair is incomplete.
See [the scoring contract](docs/scoring.md).

## Proposing a new analyzer

The admission policy is packaged in
[Proposing a new analyzer](docs/new-analyzer.md); tool maintainers are
encouraged to integrate their own analyzers, and to file issues for anything
this benchmark states wrongly about their tool. In brief:

- An adapter admits an analyzer only when the
  [four eligibility bounds](docs/adapters.md#analyzers-evaluated-and-not-adapted)
  hold: semantic data flow, local pinnable execution, retained native output,
  and publishable results.
- Eligibility is evaluated in the field, against the shipped surface of the
  pinned binary — not the prospectus.
- Every adapter pins an exact version (or asset digest), witnessed from the
  binary on every run, under the
  [pin-currency policy](docs/adapters.md#reference-tool-pin-currency).
- Scored partitions are preregistered from documentation before any result
  exists, and revised only by dated amendment.

The consolidated deliverables checklist — retained evidence, configuration
hash, capability decisions, adapter README shape, and the `src/main.rs`
touchpoints — is in the same document.

## Adapters

Once an analyzer is admitted and pinned, integrate it by following the
step-ordered [adding-an-adapter walkthrough](docs/adding-an-adapter.md):
required case inputs, the five normalized outcomes, the
anti-vacuous-negative guards, the evidence artifacts every run retains, the
validation commands, and the exact `src/main.rs` touchpoints. The
[adapter contract](docs/adapters.md) stays normative over it, and the
[docs index](docs/README.md) maps the rest of the contract surface and
defines the insider vocabulary.

## Validation

```bash
cargo fmt --check
cargo test
cargo run -- validate
cargo run -- validate-reports
```

Run `cargo run -- run-bifrost-smoke --bifrost /path/to/bifrost` when Bifrost is
available. Review the retained raw JSON before committing an updated report.

## Immutable freezes

Release and website claims must name a validated `freeze/v1` manifest. Run
`cargo run -- validate-freeze reports/freeze.json` from the exact clean Git
checkout named by the manifest. The validator checks case and fixture bytes,
adapter configuration and analyzer identities, normalized reports, and every
retained raw-evidence digest. Keep taint, value-flow, typestate, witness, and
performance dimensions separate, and never pool benchmark-controlled with
tool-native profiles. `inconclusive`, `unsupported`, and `runner-error` are
evidence outcomes, not clean negatives.

If a result is corrected, publish a new freeze with new revision and digests;
do not rewrite the previously published manifest or replace its evidence.
See the [freeze contract](docs/freeze.md).

## Governance and corrections

DataFlowBench is run on a maintainer-decides model: milestones are
deliberately small enough for one maintainer to land directly and revise
([milestones](docs/milestones.md)), and adaptation decisions are the
maintainer's. Every decision is written down against evidence, and every
correction is public: defects discovered after preregistration or freeze are
corrected by dated **amendment**, never by silent edit, numbered in a single
repository-wide `A<n>` sequence
([conventions](docs/new-analyzer.md#governance-and-corrections)). To dispute
a published outcome, use the result-dispute issue template with the report
path, case ID, raw-evidence digest, and claimed correct outcome; a dispute
that holds becomes an amendment, as OpenTaint's maintainer-driven A11 did.

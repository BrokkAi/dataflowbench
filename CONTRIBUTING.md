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

# Refreshing a released population

`--population v0.7.0` selects the exact 852 cases bound by the v0.7.0
freeze. Use this global option on every correctness, modeling, native,
cold-timing, warm-latency, and invocation-overhead command in the v0.7.1
refresh. It is an input selection, not a release branch or an exclusion by
template name. The release's case IDs, case bytes, fixture bytes, and aggregate
fixture revision are checked before command execution. A changed or missing
baseline input is an error. New cases on main remain available to the default
population and its validators.

`populations/v0.7.0.json` records the case entries from the freeze at
`0a4d8b66c1e458b10e2c6196d0e4f9622f4c8ef5`, together with that source revision
and fixture revision. The runner embeds this selection and verifies its
hard-coded SHA-256 before reading fixtures. It does not resolve a moving tag
or fetch Git objects during a run.

```bash
cargo run -- --population v0.7.0 validate
cargo run -- --population v0.7.0 run-bifrost-smoke --bifrost /path/to/bifrost
cargo run -- --population v0.7.0 validate-reports
```

Apply the same prefix to each adapter's existing documented run command and
to `measure-warm-latency` and `estimate-invocation-overhead`. The option is
process-local: pass it again for each invocation. Timing outcomes still
require the normal environment and contention evidence; population selection
does not establish an uncontended measurement. Preserve unsupported,
inconclusive, and runner-error outcomes as produced.

`validate` continues to validate the entire current corpus, including cases
reserved for v0.8.0. Runner population checks use the pinned selection while
retaining exact membership and positive/negative balance checks. The selected
fixture revision remains
`sha256:9df209ed3d7723a3ee33f2b289cf2afe34a3add781bdf2a2ac445de42b8d0151`.

After the refreshed evidence has merged, create the new freeze from clean
merged main with the same option:

```bash
cargo run -- --population v0.7.0 create-freeze \
  --report reports/<refreshed-report>.json \
  --scope release --release v0.7.1
```

Repeat `--report` for every refreshed report. Their combined case IDs must
equal the selected population exactly; an omitted baseline case or a newly
introduced kernel cannot enter this freeze unnoticed. The existing merged-main
revision requirement remains in force. Commit the new manifest, then run
`validate-freeze` and `generate-results` normally. Result generation and its
`--check` mode derive configuration paths from the validated manifest's cases,
so newer cases on main do not alter the published population. Follow the
[freeze lifecycle](freeze.md) for publication and retain the prior release's
manifest and evidence for audit.

## Prospective Swift inputs

`--population swift-synthetic-v1` selects the new 90 Swift fixtures: 66 core,
four calibration, and 20 benchmark-controlled modeling assertions. The
embedded `populations/swift-synthetic-v1.json` binds case and source bytes,
and global case validation checks its complete file set. This is a prospective
fixture selection, not a released freeze, analyzer activation, or a pooled
scored denominator. Core, calibration, and modeling remain distinct.

The existing `v0.7.0` manifest and its 852 inputs are unchanged. No Swift native,
opaque-propagator, language-extension, real-project, or reserved-track case is
implied by this selection; the [Swift contract](swift-kernel.md) records the
unresolved scope. `scripts/write-swift-population.py` authors the initial
manifest and refuses to overwrite one. Future published fixture changes need a
new population identity and explicit review.

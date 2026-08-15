# Bifrost adapter

The smoke adapter invokes Bifrost's policy CLI with `--format json` and retains
the exact report per case. Its policy-local source, sink, and sanitizer
definitions live in `policies/`; canonical cases only reference them.
Raw Bifrost witnesses are retained verbatim. Normalized `witness_checkpoints`
remain empty until the adapter can prove raw witness locations against the
canonical fixture markers; expected checkpoints are never copied into results
as if they were observed evidence.

The core smoke slice applies one balanced direct-flow template to all 13
currently supported language/dialect entries: C, C++, C#, Go, Java,
JavaScript, Kotlin, PHP, Python, Ruby, Rust, Scala, and TypeScript. A Java
propagation kernel adds 16 balanced templates across local, call/return, heap,
and control-flow strata; the Java calibration slice also covers one-hop helper
flow. Generated workspaces live outside the repository so
repository ignore rules cannot hide fixtures from Bifrost's indexer. Sanitizer
lowering is a future Bifrost CLI capability.
External semantic-model activation requires an embedding
with an explicit catalog, so the modeled-external case is reported as
`unsupported` by this CLI adapter with an explicit retained reason. It is not a
negative result.

Run from the repository root:

```bash
cargo run -- run-bifrost-smoke --bifrost /path/to/bifrost
```

## Retained v0.9.5 snapshot

The report currently checked in was produced with the exact Bifrost v0.9.5
build `a3ca30bd3fb994cc07db4abf47a2c796854882ca`. It retains 26 `reached`, 19
`not-reached`, 12 `inconclusive`, and 1 `unsupported` outcomes. Within the
32-assertion Java core, 17 of 22 decisive outcomes match their expected
polarity and 10 are inconclusive. The expression positive is a false negative;
the overwrite-kill, infeasible-branch, branch-join, and loop-kill negatives are
false positives. All eight heap assertions and both exception assertions are
inconclusive because their procedure value-flow snapshots are incomplete.

The other inconclusive pair is Ruby. Its positive case retains a finding and
witnesses, while both positive and negative cases report
`partial_discovery` because the procedure value-flow snapshot for `run` is
unknown. Both benchmark calls retain one target, but their dispatch outcomes
remain `unproven` with `open` coverage because Ruby monkeypatching and
`method_missing` keep the target set non-exhaustive. This preserves the
distinction between a candidate positive, a safe negative, and incomplete
evidence. [Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951)
tracks the final cross-language production-taint acceptance work.

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
and control-flow strata. The JavaScript parity slice uses the same template IDs
and the language-qualified `core-javascript-kernel.rqlp` policy, with any
language adaptations recorded on the canonical cases. See the [JavaScript
adaptation matrix](../../docs/javascript-kernel.md) for the syntax mapping and
the explicit exceptional-flow limitation. The Java calibration slice also
covers one-hop helper flow. Generated workspaces live outside the repository so
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

The smoke command selects only cases with an explicit Bifrost policy or
unsupported declaration. Cases for other adapters are not emitted into the
Bifrost report. Each selected case is materialized into an isolated workspace
and evaluated through Bifrost's path-based policy CLI (`--root` plus
`--policy-file`). A report with incomplete runs is normalized as `inconclusive`
even when it contains no findings; it is never interpreted as a negative.

## Retained v0.9.5 snapshot

The checked-in `reports/bifrost-smoke.json` was produced with the exact
Bifrost v0.9.5 build `0b0c5c0e2d84eb7fc75baa486f6111623b13507c`. It contains 88
normalized results: 39 `reached`, 42 `not-reached`, 6 `inconclusive`, and 1
`unsupported`. Every result's `raw_output` points to its retained per-case
Bifrost JSON under `reports/raw/bifrost/`; the normalized report and raw
reports are separate evidence layers. Raw completion and diagnostic fields are
never replaced with a synthetic `not-reached` outcome, and normalized witness
checkpoints remain empty until the adapter can prove their locations.

All 32 assertions in the Java propagation kernel match their expected polarity
(16 positive flows reached and 16 negative flows not reached). The 32
JavaScript parity assertions normalize to 12 `reached`, 16 `not-reached`, and 4
`inconclusive`. Against the canonical case polarity, 22 of the 28 complete
JavaScript outcomes match and 6 do not: positive expression, array-element,
object-separation, and same-object-field cases are false negatives; negative
infeasible-branch and loop-carried-kill cases are false positives.

The JavaScript alias-propagation pair is `inconclusive` because Bifrost reports
`partial_discovery` (the procedure value-flow snapshot is unknown). The
exception-catch pair is `inconclusive` because the run reports
`capability_incomplete` for `exceptional_control_flow`. These four incomplete
outcomes are not negative results. The other two inconclusive outcomes are the
Ruby direct-flow pair, whose positive and negative runs retain
`partial_discovery` evidence; the modeled-external Java calibration case is
the single explicit `unsupported` result. [Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951)
tracks the final cross-language production-taint acceptance work.

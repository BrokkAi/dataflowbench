# Bifrost adapter

The smoke adapter invokes Bifrost's policy CLI with `--format json` and retains
the exact report per case. Its policy-local source, sink, and sanitizer
definitions live in `policies/`; canonical cases only reference them.

The core smoke slice applies one balanced direct-flow template to all 13
currently supported language/dialect entries: C, C++, C#, Go, Java,
JavaScript, Kotlin, PHP, Python, Ruby, Rust, Scala, and TypeScript. The Java
calibration slice additionally covers one-hop helper flow. Generated workspaces
live outside the repository so repository ignore rules cannot hide fixtures
from Bifrost's indexer. Sanitizer lowering is a future Bifrost CLI capability.
External semantic-model activation requires an embedding
with an explicit catalog, so the modeled-external case is reported as
`unsupported` by this CLI adapter with an explicit retained reason. It is not a
negative result.

Run from the repository root:

```bash
cargo run -- run-bifrost-smoke --bifrost /path/to/bifrost
```

## Interim retained snapshot

The report currently checked in is an interim result for DataFlowBench commit
`2200a45e1f1dd28791545823ba4ee3afe9eaaf22`, produced by the exact Bifrost build
`adc504b3a98e00e3acb65c9b0d52a5d9734b6b2d`. It retains 8 `reached`, 8
`not-reached`, 11 `inconclusive`, and 1 `unsupported` outcomes while
[Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951) tracks the
cross-language production-taint parity work.

This snapshot is not a final accuracy result. In particular, Ruby's positive
case reports a complete zero-finding result even though its bare source call is
not selected; that is an unsafe result, not a valid clean negative, and is
tracked by [Bifrost #1956](https://github.com/BrokkAi/bifrost/issues/1956).
Likewise, incomplete results are not false negatives: they retain typed
`partial_discovery` evidence and cannot support a clean absence claim.

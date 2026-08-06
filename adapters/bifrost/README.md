# Bifrost adapter

The smoke adapter invokes Bifrost's policy CLI with `--format json` and retains
the exact report per case. Its policy-local source, sink, and sanitizer
definitions live in `policies/`; canonical cases only reference them.

The Java standalone slice supports direct flow, one-hop helper flow, and an
explicit negative. Sanitizer lowering is a future Bifrost CLI capability.
External semantic-model activation requires an embedding
with an explicit catalog, so the modeled-external case is reported as
`unsupported` by this CLI adapter with an explicit retained reason. It is not a
negative result.

Run from the repository root:

```bash
cargo run -- run-bifrost-smoke --bifrost /path/to/bifrost
```

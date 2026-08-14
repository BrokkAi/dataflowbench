# Adapter contract

An adapter executes a real supported tool surface, captures its raw output, and
normalizes only the states in `schemas/result.schema.json`: `reached`,
`not-reached`, `inconclusive`, `unsupported`, and `runner-error`.

Canonical cases never contain native rule syntax. Each adapter owns its rules,
models, command line, version discovery, configuration hash, capability notes,
and raw-evidence retention under `adapters/<tool>/`.

The initial adapter plan is:

| Tool | Initial profile | Status |
| --- | --- | --- |
| Bifrost | Java policy CLI taint slice | Implemented smoke adapter |
| CodeQL | Four-template Java taint vertical slice | Implemented adapter |
| Semgrep CE | Supported local analysis only | Planned |
| OpenTaint | Java and Kotlin profile | Planned |

No adapter may synthesize a tool result. If a supported case cannot complete,
emit `inconclusive` or `runner-error` with the raw evidence. If it is outside a
documented tool profile, emit `unsupported`; it is excluded from false-negative
interpretation.

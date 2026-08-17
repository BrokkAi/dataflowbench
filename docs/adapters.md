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
| Bifrost | Breadth baseline and Java, JavaScript, and Python propagation kernels | Implemented smoke adapter; kernel runs are reported separately |
| CodeQL | 16-template Java propagation kernel | Implemented adapter |
| Semgrep CE | Supported local analysis only | Planned |
| OpenTaint | Java and Kotlin profile | Planned |

No adapter may synthesize a tool result. If a supported case cannot complete,
emit `inconclusive` or `runner-error` with the raw evidence. If it is outside a
documented tool profile, emit `unsupported`; it is excluded from false-negative
interpretation.

The checked-in Bifrost snapshot (`reports/bifrost-smoke.json`) contains 88
normalized results from Bifrost 0.9.5 build
`0b0c5c0e2d84eb7fc75baa486f6111623b13507c`: 39 `reached`, 42 `not-reached`, 6
`inconclusive`, and 1 `unsupported`. The JavaScript profile contributes 32
balanced assertions using the Java template IDs and the
`adapters/bifrost/policies/core-javascript-kernel.rqlp` policy. Its current
outcomes are 12 `reached`, 16 `not-reached`, and 4 `inconclusive`; 22 complete
outcomes match the expected polarity and 6 complete outcomes do not. The four
incomplete runs remain `inconclusive`, never synthesized as `not-reached` or
counted as false negatives. See the [Bifrost adapter notes](../adapters/bifrost/README.md)
for raw-report separation and the per-template mismatch breakdown.

The direct-flow breadth run, Java kernel run, JavaScript kernel evidence, and
Python kernel run are distinct
adapter populations. A kernel command must select only its language and retain
the exact raw output for those cases; it must not use a direct-flow result or a
Java result as a proxy for Python. The Python kernel's 16-template balance and
construct adaptations are defined in the [Python kernel contract](python-kernel.md).

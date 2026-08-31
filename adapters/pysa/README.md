# Pysa adapter

Pysa ([facebook/pyre-check](https://github.com/facebook/pyre-check)) is
Meta's open-source Python taint analysis: `.pysa` model files declare sources
and sinks against real definitions, a `taint.config` declares the kinds and
rules, and `pyre analyze` runs a whole-program taint fixpoint. This adapter
runs it over the Python expanded core kernel — the engine's one language —
and normalizes the outcomes to the DataFlowBench contract. It completes the
queue of issue #82: Python becomes the benchmark's first five-analyzer
kernel (Bifrost, CodeQL, Joern, Semgrep CE, Pysa).

## Eligibility evaluation

`docs/adapters.md` admits an adapter only when four bounds hold. Pysa was
evaluated in the field, not from its prospectus:

1. **Semantic data flow** — holds. The engine is a real whole-program taint
   fixpoint: probed flows are reported with forward and backward trace
   roots, and interprocedural carries (argument-position, deep relay,
   recursion) are followed.
2. **Local, pinnable execution** — holds, with a field finding: the pin is a
   **pair**. The pinned pyre-check 0.10.0 client no longer carries its own
   Python front end for this path — it drives the separately released
   **Pyrefly** binary for module and call-graph resolution and refuses to
   run without one — so the adapter pins pyre-check **0.10.0** (2026-08-06,
   the newest release at evaluation time) together with Pyrefly **1.2.0**
   (2026-08-01, its contemporaneous stable release). Both run locally with
   no account, network, or service dependency.
3. **Retained native output** — holds. `pyre analyze --save-results-to`
   writes newline-delimited JSON (`taint-output.json`) carrying the bound
   models, the issues, and their traces; it is retained verbatim per case.
4. **Publishable results** — holds. pyre-check and Pyrefly are MIT-licensed,
   with no benchmark-restricting terms.

**The operable configuration was established against the binaries.** Two
silent-failure modes and one loud one were found by probe and shaped the
invocation:

- **Without a `pyrefly.toml` declaring the sources as the project, the pair
  finds nothing while exiting cleanly.** Pyrefly still type-checks the
  fixture (zero errors) and still exports its definitions, but its Pysa
  call-graph export marks every call — including a direct call to a
  same-module function — as an unresolved `EmptyPyreflyCallTarget`, so the
  taint fixpoint sees no edges and reports zero issues. A whole population
  would read as clean negatives. The runner therefore writes
  `pyrefly.toml` (`project-includes = ["src/**/*.py"]`) into every case
  workspace as part of the pinned invocation.
- **A model naming a function the fixture does not define fails loudly**
  (`Found 1 model verification error!`, exit 10) — a mis-resolved endpoint
  is a `runner-error`, never a clean negative.
- **Activation is additionally proven from the retained evidence itself**:
  the runner requires each case's `taint-output.json` to carry a bound model
  for both benchmark endpoints, the same discipline as the OpenTaint
  rule-load guard, so a `not-reached` always carries its own activation
  proof.

## Pinned tool identity, witnessed per run

| Component | Pin | Witness |
| --- | --- | --- |
| pyre-check client + `pyre.bin` | **0.10.0** | `pyre --version` → `Client version: 0.10.0`, refused on mismatch; `pyre.bin` digest measured per run |
| Pyrefly | **1.2.0** | `pyrefly --version` → `pyrefly 1.2.0`, refused on mismatch; binary digest measured per run |

Both measured digests ride in `tool_build_identity` and in each run's
`run-environment.json`. The retained runs used the official PyPI macOS arm64
wheels: `pyre_check-0.10.0-py3-none-macosx_11_0_arm64.whl` (SHA-256
`e458fa2926f462971016a421a22d0ab7658222cfc5c455d39df9ddfd85f242e1`), whose
`pyre.bin` has SHA-256
`035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3`, and
`pyrefly-1.2.0-py3-none-macosx_11_0_arm64.whl` (SHA-256
`756f669b5555090f5c1a4fef30db1785fabe657764f7e4e6dc88994dfb8ca82d`), whose
binary has SHA-256
`6b460273720d857142be562d2c0c607e8ed8e5e752ab575b5c00ea3f735d8caa`.

## Execution model

Per case, in an isolated scratch workspace that is removed after its raw
evidence is retained:

1. The declared fixture files are materialized flat under `src/`, so each
   fixture file's module name is its stem.
2. The workspace is configured: the committed `adapters/pysa/taint.config`
   and the per-case resolved models under `models/`, a `.pyre_configuration`
   naming both, and the load-bearing `pyrefly.toml`.
3. One invocation runs the analysis:

   ```text
   pyre -n --binary <pyre.bin> analyze --save-results-to <out>
   ```

   with the pinned Pyrefly's directory prepended to `PATH`, because the
   client resolves that binary by name only. The client orchestrates the
   front end and the analysis binary inside this one invocation — the
   boundary is not adapter-observable as separate subprocesses — so the
   retained phase is `total`, like Joern's and Semgrep's.

## Benchmark-controlled taint configuration

Two committed artifacts under `adapters/pysa/`, both bound into every
report's `configuration_hash`:

- **`taint.config`** — one source kind (`DfbSource`), one sink kind
  (`DfbSink`), and one rule (code **9901**). Reconciliation keys on that
  code; the config declares no other rule.
- **`models/kernel-python.pysa`** — the model template, carrying
  `__DFB_SOURCE__`/`__DFB_SINK__` (the same endpoint placeholders the
  Semgrep, OpenTaint, and Infer kernels resolve, from the same marker lines)
  plus `__DFB_SOURCE_MODULE__`/`__DFB_SINK_MODULE__`, resolved from the
  anchor files' module stems. The resolved copy is retained per case as
  `<case-id>-models.pysa`.

The template binds the sink's single parameter as `value` — every core
fixture declares `def dfb_sink(value):`, a uniformity the test suite pins —
and Pysa refuses a model whose signature does not match the definition, so a
drifted fixture fails loudly rather than silently unbinding.

## Scored partition

The whole expanded core is scored: 29 templates, 58 assertions — Python's
preregistered denominator. Pysa's documentation declares whole-program taint
analysis and fences no construct class behind a tier or a documented
capability boundary, so as with OpenTaint, Infer, and FlowDroid there is no
vendor-documented boundary to preregister `unsupported` cells from: no case
is excluded by declared capability, no capability-decision documents exist
for this population, and every incapacity the engine actually has surfaces
as a **measured mismatch** — never as a partition decision taken from an
observed result, which the adapter contract forbids.

## Outcome semantics

The five states are retained distinctly, and incompletes never become
negatives:

- `runner-error` — the analysis fails to spawn or exits non-zero (model
  verification failures surface here, loudly, with the client's output
  retained); the analysis exits cleanly but writes no `taint-output.json`;
  the evidence does not parse; or the retained evidence carries no bound
  model for one of the benchmark endpoints (the activation guard above).
- `reached` — an issue with the declared rule code whose location evidence —
  the issue's own position, or a backward-trace sink-reach position — sits
  in the case's anchor file on a callsite of the anchored sink function.
- `not-reached` — a clean, model-bound, evidence-producing run with no
  issue under the declared rule.
- `inconclusive` — endpoints that cannot be resolved from the case's own
  markers, or issues that cannot be reconciled against the sink anchor.
- `unsupported` — unused in this population; the scored partition above
  excludes nothing.

## Observed results

`reports/pysa-python-kernel.json` — 58 assertions over the full expanded
core, run whole on one machine (`run-environment.json` beside the raw
evidence). 20 `reached`, 38 `not-reached`, zero `inconclusive`,
`unsupported`, or `runner-error`; **47/58 match expected polarity** — 29/32
classic and 18/26 challenge — with ten false negatives and one false
positive.

- **The dominant false-negative family is unresolved higher-order callees,
  and it is a front-end call-graph boundary, not a taint-propagation loss.**
  The retained probe (`scripts/probe-pysa-callee-resolution.sh`,
  `reports/raw/pysa-callee-resolution-probe/`) on the dispatch-table shape
  shows the pinned pair
  resolving `dfb_source`, `leak`, `drop`, and even `dict.__getitem__` —
  then exporting the call `table[key](…)` itself as `unresolved:
  UnexpectedCalleeExpression`, so the fixpoint has no edge to carry taint
  over. The `dispatch-table`, `callback-registration`, `closure-capture`,
  `function-field`, `anonymous-implementation`, and `reflective-invocation`
  positives — every flow whose sink-reaching call goes through a
  value-carried or dynamically selected callable — are missed as one
  family, while every direct and relaying call is followed: the six-hop
  `deep-relay-chain`, `recursive-carry`, and `context-pair-depth2` pairs
  all discriminate correctly.
- **Heap-path separation splits by construct.** `heap-object`,
  `nested-access-path`, and `map-iteration` are followed and clean in both
  polarities; `alias-propagation` (taint stored through one name of an
  aliased object and read through the other), `element-object` (element
  and field separation together), and `computed-property` are missed.
- **`exception-catch`** — the value carried by a raised exception — is the
  remaining false negative, the same cell Joern's `pysrc2cpg` misses on
  this population.
- **The one false positive is `loop-carried-negative`**, the
  flow-insensitivity trip Semgrep CE's engine and Joern also report on this
  population; `infeasible-branch-negative`, the other classic
  path-sensitivity negative, is **clean** here, unlike under both of those
  engines.

## Retained artifacts

Per case under `reports/raw/pysa-python-kernel/`: the verbatim
newline-delimited evidence (`<case-id>.json`), the resolved models
(`<case-id>-models.pysa`), and the phase-timing sidecar
(`<case-id>-timing.json`, phase `total`); `-error.json` diagnostics replace
the evidence where a stage failed. Once per run: `run-environment.json` with
the witnessed pair identity.

## Reproduction

Install the pinned pair into a virtual environment and verify the wheel
digests against the identity section above:

```bash
python3 -m venv pysa-venv
pysa-venv/bin/pip install pyre-check==0.10.0 pyrefly==1.2.0
pysa-venv/bin/pyre --version
pysa-venv/bin/pyrefly --version
```

Then run the kernel (the runner re-witnesses both versions before any case):

```bash
cargo run -- run-pysa-python-kernel \
  --pyre pysa-venv/bin/pyre \
  --pyre-binary pysa-venv/bin/pyre.bin \
  --pyrefly pysa-venv/bin/pyrefly
```

The retained run used CPython 3.14.7 as the venv interpreter; the
interpreter is harness plumbing — the analysis reads sources and never runs
the fixtures.

The callee-resolution probe:

```bash
scripts/probe-pysa-callee-resolution.sh \
  --pyre pysa-venv/bin/pyre \
  --pyre-binary pysa-venv/bin/pyre.bin \
  --pyrefly pysa-venv/bin/pyrefly
```

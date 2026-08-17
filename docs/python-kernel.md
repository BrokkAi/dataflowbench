# Python semantic kernel

Issue #12 ports the Java propagation kernel to Python. The port is a
language adaptation of the same semantic contract, not a second set of Python
only scenarios. The `template_id` values below are stable benchmark
identities: Python case IDs and fixture names may be language-specific, but a
template must not be renamed, split, or silently dropped because its Java
syntax has no direct spelling in Python.

## The 16 core templates

Every Python core template has one `positive` and one `negative` case with
`score_tier: "core"`, `track: "taint"`, `language: "python"`, and the same
`model_profile`. The negative changes only the relevant semantic dimension;
it is not a second unrelated safe example.

| Stratum | Template ID | Python shape and distinction |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | A source result is passed directly to the sink. The negative calls the source separately and passes a clean value. |
| Local | `dfb-template-local-multi-step-chain` | A source is copied through several local names before the sink. The negative keeps the chain but sinks an unrelated value. |
| Local | `dfb-template-arithmetic-expression-propagation` | A source participates in an arithmetic expression. The negative computes the expression but sinks a clean literal. |
| Local | `dfb-template-local-overwrite-kill` | A source-backed local is either preserved or overwritten before the sink. |
| Calls/returns | `dfb-template-call-context-separation` | The same relay is called with tainted and clean arguments; only the selected call may reach the sink. |
| Calls/returns | `dfb-template-argument-position-separation` | A helper returns one argument. Swapping the source between the selected and ignored positions changes the expected flow. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A tainted value crosses one Python function return. |
| Calls/returns | `dfb-template-return-relay-two-hop` | A tainted value crosses two nested return relays. |
| Heap/separation | `dfb-template-object-separation` | Two `Holder` instances have the same field name; only the tainted instance may reach the sink. |
| Heap/separation | `dfb-template-same-object-field-separation` | One object has separate tainted and clean attributes. Reading the clean attribute must not inherit the other attribute's flow. |
| Heap/separation | `dfb-template-alias-propagation-separation` | `alias = original` must preserve object identity. A distinct `Holder` remains separate. |
| Heap/separation | `dfb-template-array-element-separation` | A two-element list stands in for the Java array. Writing index 0 must not taint a read from index 1. |
| Control/transfers | `dfb-template-infeasible-branch` | A constant `if False` branch contains the source, while the positive uses the reachable `if True` branch. |
| Control/transfers | `dfb-template-branch-join` | A source survives a conditional join when one branch leaves it untouched; overwriting it in both branches produces the negative. |
| Control/transfers | `dfb-template-loop-carried-kill` | A loop either carries the source through its updates or overwrites it on every iteration. |
| Control/transfers | `dfb-template-exception-catch` | A source-backed exception attribute crosses `raise` and an exact `except` handler. The negative stores a clean value in that attribute. |

The Java `dfb-template-one-hop-relay` fixture and
`dfb-template-modeled-external-summary` fixture remain calibration cases.
They are deliberately not part of the 16-template Python core denominator.

## Python adaptations

The adaptation preserves the flow question while using ordinary Python
constructs:

- **Control flow:** use constant conditions for the infeasible-branch pair,
  an optional `if` for the branch-join pair, and a bounded `for` loop (for
  example, `range(3)`) for the loop pair. The conditions and bounds are part
  of the fixture's control-flow evidence; do not replace them with a runtime
  input whose feasibility is unknown.
- **Exceptions:** define a small local exception class with a `value`
  attribute, assign either the source or a clean value, `raise` that object,
  and catch the exact class. Python exceptions are mutable heap objects, so
  this tests both exceptional transfer and the attribute access. A missing
  proof of the `raise`/`except` path is incomplete analysis, not a clean
  negative.
- **Heap and fields:** use a local `Holder` class and assign attributes after
  construction. Keep object identity, attribute names, and reads explicit so
  object separation, same-object field separation, and alias propagation each
  exercise one dimension. Do not use a global registry or a framework model
  to make the fixtures work.
- **Arrays/lists:** use a fixed two-element list with constant indices. Index
  0 and index 1 are the Python equivalent of the Java array elements for this
  kernel. List growth, slicing, comprehensions, and library calls would add
  unrelated semantics and are out of scope for this adaptation.
- **Aliases:** Python assignment binds another name to the same object. The
  positive writes through one name and reads through its alias; the negative
  reads through a separately constructed object. The distinction is object
  identity, not equal field contents.
- **Calls and locals:** normal Python functions and positional arguments are
  sufficient. Keep relay bodies transparent and avoid decorators, closures,
  imports, dynamic dispatch, or reflection; those are separate language
  extensions rather than substitutions for the core template.

Dynamic typing does not relax the contract. A source and sink marker still
identify the expected semantic endpoints, and a Python-specific spelling is
valid only when it asks the same source-to-sink question as its Java partner.

## Modeled external behavior

`dfb-template-modeled-external-summary` requires an explicitly activated
external semantic-model catalog. It is a calibration template, not one of the
16 balanced core templates. A Python bridge without an activated model is
outside the adapter's documented profile and must be reported as
`unsupported` with an explicit reason. If the tool starts with a supported,
explicit Python model, the resulting evidence may be retained as a separate
calibration or language-extension result; it must not be counted as a core
positive/negative pair.

In particular, an unresolved third-party function, missing model, partial
call graph, or incomplete witness must never be normalized as
`not-reached`. Use the result states as follows:

| Evidence state | Normalized outcome | Interpretation |
| --- | --- | --- |
| Complete witness for a positive flow | `reached` | Positive assertion satisfied. |
| Complete proof that the negative has no flow | `not-reached` | Negative assertion satisfied. |
| Analysis stopped early, has partial discovery, or cannot prove the path | `inconclusive` | Capability/evidence is incomplete; do not call it a false negative. |
| The requested language/model is outside the adapter profile | `unsupported` | Capability coverage only; not a semantic negative. |
| The command, parser, or runner failed | `runner-error` | Execution coverage only; preserve diagnostics and raw output. |

## Reporting boundaries

Reports keep these populations separate:

1. The 13-language direct-flow breadth baseline uses the direct template and
   its own per-language pair results.
2. The Java deep kernel is 16 templates and 32 core assertions.
3. The Python deep kernel is the same 16 templates and 32 core assertions,
   with Python-specific fixture paths and adaptations described above.
4. One-hop helper flow and modeled-external cases are calibration evidence and
   do not change any core denominator.

## Python CodeQL adapter

The Python CodeQL adapter is language-scoped. It selects exactly the 32 Python
core assertions under `cases/taint/python/`: the 16 template IDs in this
contract, with exactly one `positive` and one `negative` case for each. It
selects cases by their Python language, taint track, core score tier, and
`codeql` model reference; it never uses the Java kernel or the direct-flow
breadth population as a proxy.

Java and Python use separate CodeQL query packs. The Java pack remains under
`adapters/codeql/`, while the Python pack is rooted at
`adapters/codeql/python/` and owns `queries/PythonKernel.ql` plus its Python
database-schema dependency.

The reproducible command requires CodeQL CLI v2.26.3 and the pinned Python
pack `codeql/python-all@7.2.3`:

```bash
codeql pack install adapters/codeql/python --search-path /path/to/codeql-packs
codeql pack ls adapters/codeql/python --search-path /path/to/codeql-packs
cargo run -- run-codeql-python-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The runner creates an isolated Python database for each selected case, runs
`adapters/codeql/python/queries/PythonKernel.ql`, and retains the complete SARIF for
each case under `reports/raw/codeql-python-kernel/`. It writes the dedicated
normalized report to `reports/codeql-python-kernel.json`; the Java report and
`reports/raw/codeql/` are separate populations. Normalized results carry the
case's source and sink anchor markers, while the retained SARIF supplies the
CodeQL locations and diagnostic evidence used for the outcome.

The adapter preserves the five-state result model. A complete SARIF finding
for the case's anchored source-to-sink assertion is `reached`; a complete
successful analysis with no such finding is `not-reached`; partial discovery,
missing proof, or incomplete analysis is `inconclusive`; an unsupported
language/model capability is `unsupported`; and database, query, SARIF, or
runner failures are `runner-error`. Incomplete or failed runs are never
normalized as `not-reached`.

The validated Python CodeQL run used CodeQL CLI 2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/python-all@7.2.3`. Its dedicated report contains all 32 selected
assertions: 14 `reached` and 18 `not-reached`, with no `inconclusive`,
`unsupported`, or `runner-error` outcomes. 28/32 outcomes match the expected
polarity. The four mismatches are false negatives for
`alias-propagation-positive`, `array-element-positive`, and
`exception-catch-positive`, plus a false positive for `loop-carried-negative`.
This evidence is limited to the Python core kernel and does not establish
results for Java, other languages, or non-core populations.

Publish tool version, build identity, configuration, fixture revision, raw
evidence, and normalized outcomes for each population. Do not average Java,
Python, direct breadth, and calibration results into one score, and do not
use a decisive Java result as evidence that the Python adapter understood the
same construct. A Python result set is complete only when all 16 template IDs
have exactly one positive and one negative case; a missing or duplicated pair
is a validation failure.

Run the repository validator first, then the narrow kernel check:

```bash
cargo run -- validate
python3 scripts/validate-python-kernel.py
```

The narrow check is intentionally independent of any analyzer. It validates
the exact Python core population and cannot turn analyzer output into a
benchmark result.

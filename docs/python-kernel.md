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

Those sixteen are the v0.3.0 core. The thirteen challenge templates below join
them in the v0.4.0 expanded core; the two are separate populations of the same
name and are never compared number-to-number.

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

## The 13 challenge templates

[The challenge-tier preregistration](challenge-tier.md) fixed thirteen further
templates — their semantic intent, positive and negative shapes, negative
mechanisms, capability kinds, feature tags, and per-language applicability —
before any Python challenge fixture existed. All thirteen are applicable to
Python, so the expanded Python core is **29 templates and 58 assertions**.

Every challenge case carries `score_tier: "core"`,
`model_profile: "benchmark-controlled"`, and fixture provenance revision
`m3-challenge-python`. Every fixture is standard library only: `getattr`,
`setattr`, `dict`, `list`, `lambda`, nested `def`, and plain classes. Nothing
is imported.

| Stratum | Template ID | Python shape and distinction |
| --- | --- | --- |
| A — dispatch/reflection | `dfb-template-chal-reflective-invocation` | `getattr(target, name)` resolves a method from a local string constant and it is called with the source. The negative binds `name` to the sibling `drop`, which sinks a clean constant. |
| A | `dfb-template-chal-computed-property` | `setattr(holder, key, source)` then `getattr(holder, key)` with the same local key variable. The negative writes under `"alpha"` and reads under the distinct constant `"beta"`. |
| A | `dfb-template-chal-dispatch-table` | A `dict` of two functions; `table[key](source)`. The negative selects the argument-dropping entry. |
| B — higher-order | `dfb-template-chal-closure-capture` | A nested `def` closes over the enclosing function's tainted local and is returned and called after that scope has exited. The negative captures a clean local instead. |
| B | `dfb-template-chal-function-field` | The sinking function is stored in `holder.fn` and a separate `dispatch(holder, value)` reads the field and calls it. The negative dispatches through a second holder whose field holds the dropping function. |
| B | `dfb-template-chal-callback-registration` | A `Registry` instance holds a list of callables; `fire(value)` iterates and invokes them, unaware of what was registered. The negative registers a callback that ignores its parameter. |
| B | `dfb-template-chal-anonymous-implementation` | **Language-adapted** — see below. Two capture-less `lambda`s are bound to local names and one is invoked through its name. The negative invokes the argument-dropping one. |
| C — containers/paths | `dfb-template-chal-map-iteration` | The tainted value is stored under one `dict` key and retrieved by `for key, value in records.items()`, never by `get`. The negative iterates a second, disjoint `dict`. |
| C | `dfb-template-chal-nested-access-path` | A depth-3 attribute chain, `outer.middle.inner.value`, written and read at the identical path. The negative reads the sibling `outer.middle.inner.other`. |
| C | `dfb-template-chal-element-object` | A two-element `list` of instances; the tainted value sits in `items[0].value`. The negative reads `items[1].value`. |
| D — context/depth | `dfb-template-chal-deep-relay-chain` | Six module-level relays, `relay1` … `relay6`, no branching and no state. The negative feeds the identical chain the clean value. |
| D | `dfb-template-chal-recursive-carry` | `carry(value, depth)` recurses to a constant depth of 5 and returns the carried value at the base case. The negative's base case returns a clean constant instead. |
| D | `dfb-template-chal-context-pair-depth2` | `outer_tainted()` and `outer_clean()` both reach the *same* `wrapper` and the *same* `helper`; the sink takes one of the two results. The negative sinks the clean context's result. |

### Python adaptations for the challenge tier

- **`dfb-template-chal-anonymous-implementation` is language-adapted.** Python
  has no anonymous classes. The preregistration allows a `lambda` where the body
  suffices and a locally defined single-use class where the sink call cannot be
  an expression. In Python the sink call *is* an expression, so the `lambda`
  form carries the whole template body and no single-use class is needed: the
  fixture binds two capture-less `lambda`s to local names and invokes one
  through its name. Capture-less is what keeps this cell distinct from
  `dfb-template-chal-closure-capture`. This is the choice the preregistration
  requires be recorded here before the fixture is authored.
- **`dfb-template-chal-context-pair-depth2` sinks in the caller.** The
  preregistered sketch writes `outer -> wrapper -> helper -> sink`. Both outer
  contexts must be live in one fixture for the pair to test context sensitivity
  rather than dead code, so the shared `helper` returns its parameter, the
  shared `wrapper` returns `helper`'s result, and `run()` sinks one of the two
  outer results. The semantic intent is preserved exactly — the same helper is
  reached through two distinct two-deep paths and only one outer context carries
  taint — and the shape is the k = 2 extension of the classic
  `dfb-template-call-context-separation` fixture, which spells the k = 1 case
  the same way.
- **Every other cell is direct.** `getattr`/`setattr` give templates 1 and 2
  without adaptation, a `dict` of functions gives template 3, and
  `dict.items()` gives template 8, exactly as the preregistration's per-language
  classification states.

The classic Python adaptation rules above tell fixture authors to avoid
closures, dynamic dispatch, and reflection. That instruction scopes the
*sixteen-template* core, where those constructs would be substitutions for a
template that asks a simpler question. The challenge tier exists to ask about
them, and its fixtures use them deliberately.

### Which adapters ran, and which are deferred

Four adapters cover Python. Two ran over the whole expanded 58-assertion
population in this wave; two did not, and the reason is the freeze, not
coverage.

| Adapter | Expanded-population run | Report |
| --- | --- | --- |
| Joern 4.0.610 (`pysrc2cpg`) | **Ran** — whole 58-assertion population | `reports/joern-python-kernel.json` |
| Semgrep CE 1.174.0 | **Ran** — whole 58-assertion population | `reports/semgrep-python-kernel.json` |
| Bifrost v0.10.5 | **Deferred to the v0.4.0 re-run** | `reports/bifrost-python-kernel.json` |
| CodeQL CLI 2.26.3 | **Deferred to the v0.4.0 re-run** | `reports/codeql-python-kernel.json` |

**Both `reports/bifrost-python-kernel.json` and
`reports/codeql-python-kernel.json` are digest-bound by
`reports/freeze.json`** (v0.3.0). Overwriting either would invalidate a
published freeze, so neither was run here. Their committed 32-assertion
contents remain the frozen 16-template v0.3.0 evidence and say nothing either
way about the thirteen challenge templates. **Python's expanded Bifrost and
CodeQL evidence arrives with the v0.4.0 freeze-prep re-run**, which is this
repository's established re-run-at-freeze pattern. This is a deferral, not an
absence of coverage, and the v0.3.0 and v0.4.0 populations are never compared
number-to-number.

Python's challenge cases are also excluded from the Bifrost *smoke* selection,
which stays pinned at its frozen 118 cases; Bifrost's Python challenge evidence
will come from the dedicated `run-bifrost-python-kernel` population.

The two Python reports that did run carry fixture revision
`sha256:3e7a8de5e1eefb18e8166af0ccdf309bccf1d5c26026893a4513f1943926ab1f`,
which is the expanded corpus. The other languages' reports still carry the
v0.3.0 revision, because their corpora are unchanged.

### Observed results — Joern 4.0.610

`reports/joern-python-kernel.json`, `pysrc2cpg`, build identity
`joern-cli:4.0.610`, unmodified `adapters/joern/queries/kernel.sc`. All 58
assertions executed: 25 `reached`, 33 `not-reached`, and zero `inconclusive`,
`unsupported`, or `runner-error` outcomes. 48/58 match the expected polarity.

| Stratum | Assertions | Polarity match |
| --- | --- | --- |
| Classic (16 templates) | 32 | 28/32 |
| A — dispatch and reflection | 6 | 3/6 |
| B — higher-order flow | 8 | 6/8 |
| C — containers and deep access paths | 6 | 6/6 |
| D — context and depth stress | 6 | 5/6 |
| **Expanded core** | **58** | **48/58** |

The classic stratum reproduces the previous 16-template run case for case —
the same four mismatches, `alias-propagation-positive` and
`exception-catch-positive` as false negatives and `infeasible-branch-negative`
and `loop-carried-negative` as false positives — so the expansion did not
disturb the existing evidence.

Challenge mismatches, verbatim:

- `dfb-taint-python-reflective-invocation-positive`: false negative.
- `dfb-taint-python-dispatch-table-positive`: false negative.
- `dfb-taint-python-computed-property-negative`: false positive.
- `dfb-taint-python-function-field-positive`: false negative.
- `dfb-taint-python-callback-registration-positive`: false negative.
- `dfb-taint-python-deep-relay-chain-positive`: false negative.

Read as the preregistration requires:

- **Stratum A is approximation character, not skill.** Joern refuses the
  `getattr`-selected callee and the dict-selected callee — it misses both
  positives and correctly declines both negatives, which is the
  *under-approximating* position the preregistration names. On
  `computed-property` it does the opposite: it resolves the `setattr`/`getattr`
  pair through the computed key and also joins the two provably distinct
  constant keys, so the positive is right and the negative is a false positive.
  That is one engine showing both propensities on one stratum, and it does not
  rank it against anything.
- **Stratum B separates the four difficulties, which is why it was split into
  four.** Environment capture (`closure-capture`) and unnamed implementations
  (`anonymous-implementation`, the `lambda` adaptation) are both fully decided.
  Code stored in a field (`function-field`) and inversion of control
  (`callback-registration`) are both missed on the positive: a callee reached
  through `holder.fn` or through a list of registered callables is not resolved.
  Collapsing these four into one template would have reported "half" and hidden
  which half.
- **Stratum C is fully decided**, including the depth-3 access path and the
  element-plus-field pair. Read against the classic
  `same-object-field-separation` and `array-element-separation` results, this
  says Python field sensitivity here is not k-limited at depth 1 or 2.
- **Stratum D is 5/6, and the one miss is the preregistered prediction.** The
  six-hop relay's positive is `not-reached`, exactly as
  `docs/challenge-tier.md` predicted from the verified `maxCallDepth = 4`
  default; the adapter did not raise that bound, so the default is what was
  measured. Its negative is `not-reached` too — a true negative arrived at for
  the wrong reason, which the preregistration says to state rather than bank.
  Recursion (`recursive-carry`) and two-level context separation
  (`context-pair-depth2`) are both fully decided.

These are published as observed: no fixture was changed, no query was
contorted, and no case was special-cased to move a result.

### Observed results — Semgrep CE 1.174.0

`reports/semgrep-python-kernel.json`, `semgrep-oss:1.174.0`. The bounded CE
profile is unchanged and was not adjusted for this tier. All 58 assertions were
selected and balance-checked; 14 were scored and 44 were `unsupported` by
declared capability, decided from case metadata before Semgrep was invoked.
Zero `inconclusive` and zero `runner-error` outcomes; 44 retained
capability-decision documents.

| Partition | Assertions | Outcome |
| --- | --- | --- |
| Scored (`intraprocedural` partition, all classic) | 14 | 9 `reached`, 5 `not-reached`; 12/14 polarity match |
| `unsupported` — rest of the classic core | 18 | capability coverage |
| `unsupported` — challenge strata A, B, C, D | 26 | capability coverage |

**Every one of the 26 challenge assertions took the preregistered
`unsupported` partition**, which is what `docs/challenge-tier.md` said would
happen and is correct behavior for a bounded engine rather than a gap. None of
the thirteen challenge templates carries the `intraprocedural` feature tag, so
none of them enters the scored subset, and **the scored subset stays at 14**
with the same two mismatches as before — false positives on
`infeasible-branch-negative` and `loop-carried-negative`, the path sensitivity
the pinned CLI documents as Pro-only. The expansion moved the `unsupported`
remainder from 18 to 44 and moved nothing else.

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
3. The Python deep kernel was the same 16 templates and 32 core assertions in
   v0.3.0, with Python-specific fixture paths and adaptations described above.
   With the challenge row rolled out it is **29 templates and 58 core
   assertions**. The 16-template and 29-template populations are separate
   populations of the same name and are never compared number-to-number.
4. One-hop helper flow and modeled-external cases are calibration evidence and
   do not change any core denominator.

## Python CodeQL adapter

The Python CodeQL adapter is language-scoped. It selects exactly the Python
core assertions under `cases/taint/python/`: every template ID in this
contract, with exactly one `positive` and one `negative` case for each — 32
assertions over 16 templates in v0.3.0, and 58 over 29 now that the challenge
row is rolled out. The results published below are the frozen v0.3.0 ones; see
[which adapters ran](#which-adapters-ran-and-which-are-deferred) for why the
expanded CodeQL run is deferred. It
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
This evidence is limited to the **v0.3.0 16-template** Python core kernel and
does not establish results for Java, other languages, non-core populations, or
any of the thirteen challenge templates.

Publish tool version, build identity, configuration, fixture revision, raw
evidence, and normalized outcomes for each population. Do not average Java,
Python, direct breadth, and calibration results into one score, and do not
use a decisive Java result as evidence that the Python adapter understood the
same construct. A Python result set is complete only when every template ID in
the language's current core denominator — all 29 of them — has exactly one
positive and one negative case; a missing or duplicated pair is a validation
failure.

Run the repository validator first, then the narrow kernel check:

```bash
cargo run -- validate
python3 scripts/validate-python-kernel.py
```

The narrow check is intentionally independent of any analyzer. It validates
the exact Python core population and cannot turn analyzer output into a
benchmark result.

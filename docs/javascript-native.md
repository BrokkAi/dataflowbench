# JavaScript tool-native probe set

This is wave N1's JavaScript row: the twelve fixtures of
[the tool-native model profile](native-profile.md), the vendored Semgrep
activation snapshot its partition needs, and the four runs.

It measures the **product**, not the engine. Every fixture here names real Node
and ECMAScript APIs by their real identities, and every model under test is one
a vendor ships. A miss says the shipped model set does not cover an API; it says
nothing about whether the engine could have followed the flow had it been told —
which is the opposite of what a miss means in
[the benchmark-controlled matrix](javascript-modeling.md).

**JavaScript's native denominator is 6 templates / 12 assertions**, on the
`modeling` tier at `model_profile: "tool-native"`, with its own scorecards. No
number in this document is ever pooled with the 12 templates / 24 assertions of
the benchmark-controlled row, even though the two share a tier and a language,
and the two run on deliberately different CodeQL library resolutions —
`javascript-all@2.10.0` here, bundled by the pinned query pack, against the
adapter's `javascript-all@2.9.0` there. A corpus-wide check asserts the two
populations never cross-select.

Nothing here amends a template definition. The six templates, their platform-API
identities, their negative shapes and mechanisms, and the per-tool partition
were fixed before any of these fixtures existed. This row contributes one
amendment,
[A6](native-profile.md#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot),
which resolves Semgrep CE's six *to be verified at vendoring* cells against a
pinned snapshot and moves none of them.

## What is committed

| Artifact | Path |
| --- | --- |
| Cases and fixtures | `cases/taint/javascript/native-*-{positive,negative}/` |
| Vendored Semgrep snapshot | `adapters/semgrep/native/javascript/` (30 rules, `provenance.json`, upstream `LICENSE`) |
| Reports | `reports/{bifrost,codeql,joern,semgrep}-javascript-native.json` |
| Raw evidence | `reports/raw/{bifrost,codeql,joern,semgrep}-javascript-native/` |

No model artifact is committed, and none could be: `tool_model_references` is
empty on all twelve cases, and
[the no-benchmark-models gate](native-profile.md#the-activation-rule) reads each
tool's pinned activation shape before the analyzer is touched and refuses a run
that names one.

## Per-template realization

Every fixture is a single `probe.js`, `node --check` clean, using nothing but
Node and the ECMAScript standard library — no dependency, no manifest, no build
step. Each is one function plus its call, so the flow under test is the only
flow in the file.

The pinned module-specifier spelling is the **bare** one,
`require("child_process")` and `require("path")`, per
[the native-binding trap](native-profile.md#the-native-binding-trap). CodeQL
resolves `["node:" + path, path]` and sees both spellings as one module; a
pattern rule that matches the bare specifier literally does not see the prefixed
one. A tool that recognizes only one spelling is a finding about that tool.

### 1. `dfb-template-native-source-sink` — category S

`process.env.DFB_INPUT` reaches `child_process.execSync` in one hop.

The negative replaces the value with a clean constant local and **keeps the
environment read**, unused, beside it. The sink is present and identical in both
cells, so a rule that fires on the existence of a `child_process` call cannot
bank a true negative it did not earn —
[the sink-existence rule](native-profile.md#sink-existence-only-findings-and-how-they-score).

### 2. `dfb-template-native-propagator` — category P

The environment read is joined with a constant through `path.join` from
`require("path")`, and the result reaches the same sink. `path.join`'s body is
inside Node, so only a shipped propagator summary carries the value across.

The negative performs the *same join on the same tainted value* into a variable
that goes nowhere, and sinks a second `path.join` of two constants. Both cells
contain a tainted `path.join` and an `execSync`; only the positive connects
them.

### 3. `dfb-template-native-sanitizer` — category Z

`"printf " + value` reaches the sink in the positive. The negative is the
identical flow with `encodeURIComponent(value)` in the middle.

This is the template
[the preregistration warned about in advance](native-profile.md#3-dfb-template-native-sanitizer--category-z),
and the warning was correct — see the results.

### 4. `dfb-template-native-summary` — category O

`Buffer.from(value).toString("base64")` then
`Buffer.from(encoded, "base64").toString()`, and the round-tripped value reaches
the sink. Both halves must be summarized for the flow to survive.

The negative round-trips a fresh constant into the same sink and keeps the
environment read present and unused.

### 5. `dfb-template-native-entrypoint` — category E

`process.argv[2]` reaches the sink. No framework, no registration — Node's own
convention for where a program's arguments arrive.

The negative declares a constant local **beside** the argv read in the same
function and sinks that instead; the argv read is present and goes nowhere.

### 6. `dfb-template-native-persistence` — category B

`process.env.DFB_STORED = process.argv[2]`, then a read of
`process.env.DFB_STORED`, then the sink. The negative writes the same key and
reads a **distinct** key, `DFB_OTHER`, into the same sink —
`negative_mechanism: field-separation`.

Both cells therefore contain a write, a read of `process.env`, and an
`execSync`. Only the positive's read is of the key that was written.

## Anchor reconciliation

Every other population in this benchmark declares its own endpoint function and
hangs the marker on that declaration, so the runner resolves a declared name and
then finds the lines that call it. **This profile has no declared entity**: the
sink is `child_process.execSync` and its body is inside Node. Markers therefore
sit directly on the line that calls the platform API, and that line *is* the
callsite. `native_sink_anchor_locations` resolves it, and a test asserts that
all twelve cases resolve to a line containing `execSync(`.

An anchor is not a model. It decides which finding belongs to which assertion;
it tells the analyzer nothing about what a source or a sink is.

One reconciliation rule differs from the rest of the benchmark, and it follows
from what a native run analyzes. Elsewhere the runner points CodeQL at a single
adapter query, so any finding is a finding about the assertion and one that does
not land on the anchor means the reconciliation is untrustworthy — hence
`inconclusive`. A native run points CodeQL at a whole shipped suite (103 rules
resolved for JavaScript), which asks about everything from weak hashing to
regular-expression denial of service. A finding those queries produce elsewhere
in the fixture is a different query answering a different question. It is
**retained in the diagnostics and does not make the cell `reached`**; what it
never does is become evidence of a flow. Ambiguity — a malformed location, or
one finding matching two anchors — stays `inconclusive` as everywhere else.

In this run the rule was not load-bearing: every finding CodeQL produced landed
on the case's own sink anchor, and no case recorded an away-from-anchor
diagnostic.

## Results

Run sequentially against the pinned toolchain — Bifrost v0.10.6, CodeQL CLI
2.26.3, Joern 4.0.610, Semgrep CE 1.174.0 (`--oss-only`) — on 2026-08-27. Every
outcome is retained in `reports/<tool>-javascript-native.json` with its raw
evidence under `reports/raw/<tool>-javascript-native/`.

### Outcome distribution

| Adapter | Scored | `reached` | `not-reached` | `inconclusive` | `unsupported` | Correct |
| --- | --- | --- | --- | --- | --- | --- |
| Bifrost v0.10.6 | 0 | 0 | 0 | 0 | 12 | — |
| CodeQL 2.26.3 | 12 (all six) | 7 | 5 | 0 | 0 | **10 / 12** |
| Joern 4.0.610 | 0 | 0 | 0 | 0 | 12 | — |
| Semgrep CE 1.174.0 | 0 | 0 | 0 | 0 | 12 | — |

Configuration hashes: Bifrost `0badb216…`, CodeQL `a2484ca5…`, Joern
`3b223e29…`, Semgrep `d6e15fba…`.

Three of the four adapters ran **without being invoked at all**. Their cells are
declined by the preregistered partition, decided from the template identity
before any binary is touched, and each of the twelve retained evidence documents
carries the preregistration's own rationale verbatim with
`"evidence_kind": "retained-capability-decision"`. That is capability coverage.
It is never a negative, it reduces no denominator, and it is not a score of
zero.

The Semgrep column deserves the distinction stated plainly. Its snapshot was
vendored, its provenance gate passed, its rule text was read cell by cell — and
the reading concluded that no vendored rule can bind a platform source, so all
six cells were **retained** unsupported by
[Amendment A6](native-profile.md#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot).
Semgrep declined this profile for JavaScript; it did not fail it.

### CodeQL, per template

The only scored column. Read it against
[the 50% blind baseline](scoring.md#balanced-pairs-and-the-blind-baseline), not
against zero.

| # | Template | Cat. | Positive | Negative | Correct |
| --- | --- | --- | --- | --- | --- |
| 1 | `native-source-sink` | S | `reached` — TP | `not-reached` — TN | **2 / 2** |
| 2 | `native-propagator` | P | `reached` — TP | `not-reached` — TN | **2 / 2** |
| 3 | `native-sanitizer` | Z | `reached` — TP | `reached` — **FP** | 1 / 2 |
| 4 | `native-summary` | O | `reached` — TP | `not-reached` — TN | **2 / 2** |
| 5 | `native-entrypoint` | E | `reached` — TP | `not-reached` — TN | **2 / 2** |
| 6 | `native-persistence` | B | `not-reached` — **FN** | `reached` — **FP** | 0 / 2 |

**True-positive rate 5/6; false-positive rate 2/6.** Both are published, and
neither is published alone: a positive cell answered by a rule that does not
reason about flow earns its true positive and tells us nothing, which is why the
pair is the instrument.

The rules that fired are `js/command-line-injection` and
`js/indirect-command-line-injection`, both from
`codeql/javascript-queries@2.4.4`'s `javascript-security-extended.qls`, with
`--threat-model=local` enabling the shipped `environment` and `commandargs`
groups. Without that option templates 1, 5, and 6 would have been decided by
CodeQL's default `remote`-only threat model and every cell would have missed for
a reason that has nothing to do with coverage. The option configures shipped
models; it supplies none.

### The two mismatches, in full

**Template 3, negative — false positive. `encodeURIComponent`'s credit is
query-family-scoped, exactly as preregistered.** The negative passes the
environment value through `encodeURIComponent` before concatenating it into the
command, and CodeQL reports `js/indirect-command-line-injection` anyway. This is
not a fixture defect and not an engine failure. In the shipped
`javascript-all` library, `encodeURIComponent` is a sanitizer for XSS
(`Xss.qll`) and for request forgery (`RequestForgeryCustomizations.qll`), while
`TaintTracking.qll` lists it among the taint-**preserving** steps for everything
else — and command injection is everything else. The preregistration
[stated this in advance](native-profile.md#3-dfb-template-native-sanitizer--category-z)
precisely so that a disappointing cell could not later be re-read as a benchmark
bug. It is a publishable product fact about where a sanitizer's credit is
scoped.

It is also, on the merits, a defensible product position:
`encodeURIComponent` is a URL-component encoder and is *not* a shell quoter. The
measurement is not that CodeQL is wrong; it is that the shipped model set does
not distinguish "sanitized for this sink" from "sanitized", and the balanced pair
is what makes that visible.

**Template 6, both cells wrong — and the two failures have the same cause.**

The *positive* misses. `process.env.DFB_STORED = process.argv[2]` followed by a
read of `process.env.DFB_STORED` produces **zero findings from all 103 rules**,
even though both endpoints are individually modeled: `process.argv` is a shipped
`commandargs` source, `process.env` is a shipped `environment` source, and
`execSync` is a shipped sink. The write/read pair through the process
environment is not linked, and the presence of a local write appears to prevent
the read from being treated as a plain environment source, so the value that a
bare `process.env` read would have carried is lost at the store boundary.

The *negative* fires. It writes `process.env.DFB_STORED` and reads
`process.env.DFB_OTHER` — a distinct key, so no flow exists — and CodeQL reports
both `js/command-line-injection` and `js/indirect-command-line-injection` on the
`execSync` line. The read of an unwritten key is a plain shipped environment
source, and the model has no key discrimination to apply, because it is not
looking at keys at all.

Put together: **the store link is absent in the direction where it would find a
real flow, and the source model fires in the direction where the key says there
is none.** That is exactly the hazard
[the preregistration named for this template](native-profile.md#6-dfb-template-native-persistence--category-b),
down to its wording — a tool that treats the read as a source rather than as a
store-read takes a false positive on the negative, "because the distinct key is
exactly what it is not looking at." The only thing the run adds to the
prediction is the positive-side half: here the store boundary does not merely
fail to *link*, it also suppresses the source the read would otherwise be.

### What the numbers do and do not say

- **10/12 is coverage, not accuracy.** It says CodeQL's shipped JavaScript model
  set binds `process.env`, `process.argv`, `path.join`, the `Buffer` base64 round
  trip, and `child_process.execSync` well enough to decide five of six templates.
  It says nothing about the engine, which
  [the benchmark-controlled row measures separately](javascript-modeling.md) and
  which scored 24/24 there.
- **The floor was cleared.** Template 1 is
  [the profile's floor](native-profile.md#1-dfb-template-native-source-sink--category-s):
  a tool that misses it ships no usable native taint coverage for the language.
  CodeQL clears it.
- **The base64 round trip survived**, which the preregistration flagged as the
  template most likely to miss. `javascript-all@2.10.0` summarizes both halves.
- **Three adapters have no number here at all**, and that is the point of the
  `unsupported` mechanism. Bifrost's standalone policy CLI ships no source or
  sink endpoint catalog (bifrost-dev #2620, #2691); Joern's `DefaultSemantics`
  ships flow constraints with no source or sink catalog, and the version-pinned
  `joern-scan` query bundle ships no JavaScript query package at all (Amendment
  A26, which retired the earlier unpinnable-asset grounds); Semgrep's vendored
  rules bind only framework and parameter sources.
  Each is a statement about *product packaging*, not about an engine — the
  benchmark-controlled row scores Joern on 16 assertions and Semgrep on 10 using
  the same engines.
- **Nothing here is pooled with anything.** Not with the benchmark-controlled
  modeling row, not with the propagation kernel, not across the two profiles'
  shared tier.

## The three-way distinction

[The modeling matrix's distinction](modeling-matrix.md#the-three-way-distinction)
applies with one substitution:
[*missing model* becomes *missing activation artifact*](native-profile.md#outcome-honesty),
and it is a hard error rather than an outcome. In this row:

- **Unsupported activation** — 36 assertions across Bifrost, Joern, and Semgrep.
  Decided from the template identity before the tool was invoked, rationale
  retained verbatim.
- **Incomplete analysis** — none. No case recorded `inconclusive`.
- **Runner failure** — none.
- **Coverage miss** — one, template 6's positive: a plain `not-reached` by an
  activated model set, which on a positive cell is a false negative and is
  exactly the number this profile is built to publish.

The missing-activation-artifact gate was exercised for real: before
`adapters/semgrep/native/javascript/provenance.json` existed, the Semgrep native
run refused to start rather than reporting the vendor's coverage as zero for a
reason that had nothing to do with the vendor.

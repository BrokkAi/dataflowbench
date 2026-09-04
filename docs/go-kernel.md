# Go propagation kernel

Issue #36 ports the sixteen scored Java propagation templates to Go, as
classified in the [applicability matrix](applicability-matrix.md). The Go cases
keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to Go syntax. Every
scored Go template has exactly one `positive` and one `negative` `core` case, so
the classic Go core denominator is 16 templates and 32 assertions, exactly as the
matrix fixes it. The [challenge-tier expansion](#challenge-tier-expansion) below
takes it to 29 templates and 58 assertions; the two are separate populations.

| Stratum | Template ID | Go adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | A local `int` is either preserved or reassigned to a constant before the sink. |
| Local | `dfb-template-local-multi-step-chain` | `:=` locals carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | Go integer arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One `relay` function is called with a tainted and a clean value; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | `chooseFirst` returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop function return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two nested function returns preserve the two-hop depth. Go's multiple return values are not needed to express any calls/returns template. |
| Heap/separation | `dfb-template-object-separation` | **Language-adapted.** Two `Holder` struct values with the same field name stand in for the distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | **Language-adapted.** One `Holder` struct has separate `Tainted` and `Clean` fields. |
| Heap/separation | `dfb-template-alias-propagation-separation` | **Language-adapted.** `alias := &original` creates a pointer alias to the same struct; a second struct literal (`distinct`) stays a separate object. |
| Heap/separation | `dfb-template-array-element-separation` | **Language-adapted.** A `[2]int` array with distinct constant indices stands in for the Java array. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the tainted path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A three-iteration `for` loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | **Language-adapted.** `panic(v)` with a deferred `recover()` replaces Java's checked exception; see below. |

Every language-adapted cell above is exactly the adaptation the matrix
prescribes, and this contract records no deviation from it.

All Go fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names in `package dataflowbench`, mirroring the Go direct-flow fixture
already in the breadth slice. Each fixture is a single gofmt-clean `.go` file
that compiles with `go build` and imports nothing. Adapters may lower those
endpoints through their own models, but the case metadata stays
analyzer-neutral and reports retain only observed evidence.

## `panic`/`recover` as the exception-catch construct

Go has no exception type and no `throw`/`catch`. Its one construct that carries
a value out of a function through a control transfer distinct from a normal
return is `panic`, whose value is delivered to a deferred `recover()`. The
positive case panics with the controlled value and sinks what `recover` returns;
the negative panics with a constant while the controlled value is discarded, so
the pair differs only in the value that crosses the transfer:

```go
defer func() {
	if recovered := recover(); recovered != nil {
		dfb_sink(recovered.(int))
	}
}()
panic(dfb_source()) // DFB-WITNESS: exception-catch-panic
```

This follows the JavaScript precedent of replacing Java's checked exception
class with the language's native transfer construct, and preserves the
template's semantic intent: a value that reaches the sink only by travelling
through a non-local control transfer.

**If a pinned analyzer cannot model `recover`'s return value, that is recorded
as capability evidence — a false negative on the positive case, or an
`inconclusive`/`unsupported` outcome — and never as a silent redesign of the
case into a construct the tools happen to handle, and never as a clean
negative.** Both pinned analyzers do in fact fail this pair; the observed
results below report that as a capability gap, and the fixtures are unchanged.

## Go's unused-variable rule

Go rejects an unused local variable at compile time, where C# and Java only
warn. Three negatives therefore write a discarded binding (`_ = third`,
`_ = computed`, `_ = alias`) or discard a relay result directly
(`_ = relay(dfb_source())`) where the C# kernel simply leaves the local unused.
This changes no flow: the discards are the compiler's requirement for keeping
the negative minimally different from its positive, not an extra propagation
step or a sanitizer.

## Challenge-tier expansion

[The challenge tier](challenge-tier.md) preregistered thirteen further
propagation templates before any fixture existed. All thirteen are applicable to
Go — ten directly, three language-adapted — so the Go core denominator grows
from 16 templates / 32 assertions to **29 templates / 58 assertions**. The
challenge cases carry `score_tier: "core"` — there is no separate tier — and
their fixture provenance revision is `m3-challenge-go`.

The v0.3.0 sixteen-template core and this expanded core are different
populations and are never compared number to number.

### Adaptation notes

The preregistration classifies three Go cells as **language-adapted**, and
prescribes each adaptation itself; this contract records no deviation from it.
The realizations, so a reader can check each fixture against the template rather
than against a guess:

| Stratum | Template ID | Go realization |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | **Language-adapted**, exactly as the matrix prescribes: `reflect.ValueOf(receiver{}).MethodByName(name).Call([]reflect.Value{reflect.ValueOf(dfb_source())})`, with `name` a local `string`. Go has no non-reflective way to name a callee at run time, and `reflect` is stdlib. The negative points `name` at the sibling method `Drop`, which ignores its argument and sinks a constant. Both methods are exported because `MethodByName` resolves exported methods only. |
| A | `dfb-template-chal-computed-property` | **Language-adapted** through `reflect`: `reflect.ValueOf(&holder).Elem().FieldByName(key).SetString(dfb_source())` and a matching `FieldByName(key).String()` read. Go has no computed member syntax; this is the same adaptation Java makes through `java.lang.reflect.Field`, and it keeps the member located by a run-time name. The negative writes under `"Payload"` and reads the provably distinct `"Other"`. The address-of and `.Elem()` are what make the struct field settable, not an extra propagation step. |
| A | `dfb-template-chal-dispatch-table` | Direct. A package-level `map[string]func(value string)` with two func literals; the entry is fetched as a first-class value (`selected := table[key]`) and then invoked, which is what separates it from the reflective method call above. |
| B | `dfb-template-chal-closure-capture` | Direct. `makeHandler() func()` captures the tainted local and returns `func() { dfb_sink(captured) }`, invoked by the caller after the local has left scope. The negative captures a clean local; the source call stays live. |
| B | `dfb-template-chal-function-field` | Direct. Two `*Holder` values each carry a `Fn func(value string)` struct field; a separate `invoke(target *Holder, value string)` reads the field and calls it. The negative hands `invoke` the second holder. |
| B | `dfb-template-chal-callback-registration` | Direct. `Registry{hooks []func(value string)}`, a `register` function that appends, and a `fire` driver that ranges and invokes. No framework, twenty lines of language. |
| B | `dfb-template-chal-anonymous-implementation` | **Language-adapted**, exactly as the matrix prescribes: the `http.HandlerFunc` idiom without importing `net/http`. A locally declared `type HandlerFunc func(value string)` carries a `Handle` method satisfying the one-method `Handler` interface; an anonymous func literal is converted to it and invoked through the interface-typed variable. Go has no anonymous type that implements an interface inline; this is the idiomatic equivalent. Neither literal captures anything, which keeps it distinct from closure capture. |
| C | `dfb-template-chal-map-iteration` | Direct. `for _, value := range carrier` over a `map[string]string`, never a keyed get. The negative ranges a second, disjoint map. |
| C | `dfb-template-chal-nested-access-path` | Direct. `a.B.C.Value` written and read at depth 3 through three nested structs; the negative reads the sibling `a.B.C.Other`. |
| C | `dfb-template-chal-element-object` | Direct. A `[]Item` of structs; the negative reads `items[1].Value` after `items[0].Value` was written. `negative_mechanism` stays `field-separation`, on the precedent the classic `dfb-template-array-element-separation` Go cell already sets. |
| D | `dfb-template-chal-deep-relay-chain` | Direct. `relay1` … `relay6`, package-level, `func(value string)` throughout, no branching or state, with the sink inside `relay6`. The negative feeds the identical chain a clean constant. |
| D | `dfb-template-chal-recursive-carry` | Direct. `carry(value string, depth int) string` recursing to `depth == 0` from 5; the negative's base case returns a clean constant instead of the carried one. |
| D | `dfb-template-chal-context-pair-depth2` | Direct, per [Amendment A1](challenge-tier.md#amendments): one `helper` reached through `outerTainted -> wrapper -> helper` and `outerClean -> wrapper -> helper`, with `helper` returning its argument and the caller sinking the selected result. Both paths are live in both fixtures; only which returned value reaches `dfb_sink` differs. |

The `reflect` import in the two stratum-A fixtures is the only import anywhere
in the Go population. It is the standard library, so the tier's stdlib-only
fairness constraint holds, and both fixtures were executed to confirm the
adaptation carries the value it claims to: the positives print the tainted
value at the sink and the negatives print the clean constant.

Go's unused-variable rule reaches the challenge fixtures the same way it reaches
the classic ones (see above). Seven negatives and two positives write a
discarded binding — `_ = tainted`, `_ = clean`, `_ = other`, `_ = dropHandler` —
where a language that only warns would leave the local unused. This changes no
flow: the discard is the compiler's price for keeping each negative minimally
different from its positive, not a propagation step and not a sanitizer.

All twenty-six fixtures are single, import-minimal, gofmt-clean `.go` files in
`package dataflowbench`, and every one compiles with `go build` under the host
toolchain this kernel records (go1.26.0, darwin/arm64), one fixture per module
workspace — one at a time because every fixture declares `dfb_source`, `dfb_sink`,
and `run` at package scope, so compiling them together would collide on those
names rather than find a defect.

### Adapter coverage of the expanded population

One adapter was re-run over the whole 58-assertion population for this
expansion. Two are deferred by the freeze rule, and one does not cover Go at
all. None of the three is a gap in what this kernel measures, and the difference
between them matters:

| Adapter | Expanded run | Report |
| --- | --- | --- |
| Semgrep CE 1.174.0 | Yes | `reports/semgrep-go-kernel.json` |
| Bifrost v0.10.5 | **Deferred (freeze-bound)** | `reports/bifrost-go-kernel.json` |
| CodeQL 2.26.4 | **Deferred (freeze-bound)** | `reports/codeql-go-kernel.json` |
| Joern 4.0.617 | **No Go slice exists** | — |

**Both Bifrost and CodeQL are deferred, and both for the same reason.**
`reports/bifrost-go-kernel.json` and `reports/codeql-go-kernel.json` are two of
the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so this
change must not overwrite either: **expanded Bifrost and CodeQL evidence for Go
is pending the v0.4.0 freeze-prep re-run**, on this repository's established
re-run-at-freeze pattern. The retained reports below remain the valid
32-assertion classic snapshots, and they describe a *different population* from
the expanded one. Deferral is not absence of coverage: both engines cover Go,
both already produced decisive Go evidence at the classic denominator, and both
will attempt all 58 assertions at v0.4.0. This wave simply had no freeze-legal
file to write them to.

**Joern has no Go slice, and this wave did not invent one.** The pinned
`joern-v4.0.617` adapter covers Java, JavaScript, Python, Ruby, PHP, and Rust.
Joern's Go frontend, `gosrc2cpg`, lives upstream and is **not built into the
pinned distribution**, so there is no `run-joern-go-kernel` command, no Go
selection, and no `reports/joern-go-kernel.json` — and standing a slice up is a
new adapter change, not a side effect of landing fixtures. Go therefore has no
Joern evidence at any denominator, classic or expanded.

### Semgrep CE 1.174.0 — expanded core

`reports/semgrep-go-kernel.json`. The whole 58-case population is selected and
balance-checked, and the bounded profile then decides what is scored, from case
metadata, before Semgrep is invoked.

| Stratum | Assertions | Scored | `unsupported` | Polarity match (scored) |
| --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 14 | 18 | 12/14 |
| Challenge (13 templates) | 26 | 0 | 26 | n/a |

Whole-population outcome distribution: 9 `reached`, 5 `not-reached`, 44
`unsupported`, zero `inconclusive`, zero `runner-error`.

**All twenty-six challenge assertions take the preregistered `unsupported`
partition**, exactly as [the challenge tier](challenge-tier.md) predicted: no
challenge template carries the `intraprocedural` feature tag, so none is inside
the documented CE local-taint profile, and each retains its own
`*-unsupported.json` capability-decision document naming the declared capability
and the boundary it falls outside, citing the preregistered per-template
rationale rather than the generic tag rule. The scored subset therefore stays at
**14 assertions and 12/14**, unchanged from the classic run — the two mismatches
are still the false positives on `dfb-taint-go-infeasible-branch-negative` and
`dfb-taint-go-loop-carried-negative`, the path sensitivity the pinned CLI sells
as Pro. Comparing the retained report before and after this expansion, **not one
of the 32 classic outcomes moved**. The partition was not adjusted for this
expansion, and twenty-six declined assertions are coverage, never twenty-six
false negatives.

The expanded report carries fixture revision
`sha256:7f37b99ddab7764a8536112c09ff7c8d77e0b02f7786abde65dfbaf3654d9949`,
configuration hash
`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100` — unchanged
from the classic run, because no rule file was touched — and tool build identity
`semgrep-oss:1.174.0`. Reports at different fixture revisions are not pooled.

### What this wave does and does not establish

Stated honestly, because the deferral makes it easy to overclaim: this wave
establishes that the Go challenge fixtures exist, compile, are gofmt-clean, and
are selected and balance-checked by the population machinery, and it establishes
one adapter's expanded-population behavior — Semgrep CE's, which is a declared
capability boundary rather than an analysis result. It establishes **nothing**
about how well any engine follows Go taint through `reflect`, higher-order code,
containers, or depth. That evidence arrives with the v0.4.0 re-run of the two
deferred adapters, and until then Go's challenge strata have no analysis
outcomes at all.

## Case population and the frozen direct pair

The Go core population is the `taint`/`core` cases under `cases/taint/go/` — 32
assertions classically, and **58** now that the thirteen challenge templates
have rolled out. Thirty of the classic cases were authored for this kernel with
`fixture_provenance.revision` `m2-go-kernel`, and the twenty-six challenge cases
with `m3-challenge-go`. The direct-propagation pair (`dfb-taint-go-direct-positive` and
`dfb-taint-go-direct-negative`) predates it: it is the Go member of the
13-language direct-flow breadth slice and is frozen byte-for-byte in the
published v0.2.0 manifest (`reports/freeze.json`). Its `case.json` therefore
keeps `fixture_provenance.revision` `m1a-direct-core`, keeps the breadth policy
reference `adapters/bifrost/policies/core-direct.rqlp`, and carries no CodeQL
model reference.

Editing those two files would invalidate the published v0.2.0 evidence, so the
runners accommodate them instead:

- the Bifrost Go selector accepts either `core-go-kernel.rqlp` or the breadth
  `core-direct.rqlp` policy for a Go core case, and evaluates each case through
  the policy it declares;
- the CodeQL Go selector defaults a Go core case with no `codeql` model
  reference to this kernel's query, and rejects any Go core case that names a
  different query.

The same case is a member of two populations, but its results are never pooled:
the breadth result lives in `reports/bifrost-smoke.json` and the kernel result
in the dedicated Go reports below.

## Bifrost selection and reproduction

The Bifrost Go slice uses the language-qualified policy
`adapters/bifrost/policies/core-go-kernel.rqlp`, whose source and sink selectors
are `(language go (call :callee (name "dfb_source")))` and
`(language go (call :callee (name "dfb_sink")))`, with argument index 0 as the
dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-go-kernel --bifrost /path/to/bifrost
```

The command selects the whole Go core population — 32 assertions classically,
58 with the challenge templates rolled out — materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-go-kernel.json`, and retains the verbatim per-case Bifrost JSON
under `reports/raw/bifrost-go-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

**This command was deliberately not run for the challenge expansion.**
`reports/bifrost-go-kernel.json` is freeze-bound by v0.3.0, so running it now
would overwrite frozen evidence; the expanded run is deferred to the v0.4.0
freeze-prep re-run, as recorded above.

## CodeQL selection and reproduction

The CodeQL Go vertical slice is the whole Go `taint`/`core` population — 32
assertions classically, and **58** now that the thirteen challenge templates
have rolled out. The retained snapshot below is the classic 32, because the
expanded run is deferred to v0.4.0 by the freeze rule. Every selected case is
analyzed with the dedicated query:

```text
adapters/codeql/go/queries/GoKernel.ql
```

The query is owned by the dedicated Go pack manifest at
`adapters/codeql/go/qlpack.yml`; the Java, JavaScript, TypeScript, Python,
Kotlin, and C# packs are separate. The runner must not select any other
language, calibration cases, or the direct-flow breadth population.

Registry retrieval of the Go pack succeeded for the pinned CLI, so no source
workspace fallback was needed:

```bash
codeql pack install adapters/codeql/go
cargo run -- run-codeql-go-kernel --codeql /path/to/codeql --go /path/to/go
```

`codeql pack install` resolved `codeql/go-all@7.2.3` for CodeQL CLI 2.26.4
(build SHA `6b1e4dee94adb20f90a671f3fc9e04be32eecf65`); the complete transitive
set is committed in `adapters/codeql/go/codeql-pack.lock.yml`. If registry
retrieval is unavailable, a matching official source workspace or CLI bundle
pack root passed through `--codeql-packs` is a valid reproduction input, as
documented for the [JavaScript kernel](javascript-kernel.md).

### Why the Go databases are built, not build-free

CodeQL 2.26.4 rejects `--build-mode=none` for Go outright ("Go does not support
the none build mode"), so a Go database can only be created from an observed
build. Autobuild would work, but it synthesizes its own module manifest and runs
`go get ./...`, which makes extraction depend on the network. The runner
therefore uses `--build-mode=manual` with the command `go build ./...` and
writes a minimal module manifest into each per-case workspace itself:

```text
module dataflowbench

go 1.21
```

That manifest is extraction scaffolding, not case data: it lives only in the
temporary workspace, is never committed beside a fixture, and keeps the case
metadata analyzer-neutral. The fixtures import nothing, so the build is
hermetic and offline. The observed toolchain was go1.26.0 (darwin/arm64).

For each case the runner creates one cold Go database from the declared fixture
file only, runs the dedicated query, and removes the temporary workspace and
database after retaining the evidence. The normalized report is
`reports/codeql-go-kernel.json` and the raw SARIF (or raw runner diagnostics
when CodeQL cannot produce SARIF) is retained per case under
`reports/raw/codeql-go-kernel/`.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor. That
marker identifies the anchored sink function declaration; Go declares a function
name immediately before its parameter list and spells a call the same way C#
does, so Go reuses that dialect of the shared reconciler: the declared name is
the identifier preceding the parameter list, and a SARIF result is accepted when
it lies in the same fixture file on a line that calls that function. The result
need not be on the marker's own line. Query path evidence identifies the
`DFB-SOURCE:` to sink flow, and normalized results retain both anchor sets.

A successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing, ambiguous, or unmappable location
evidence is `inconclusive`, an explicitly unsupported capability is
`unsupported`, and a database, query, SARIF, or runner failure is
`runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 16 balanced assertions.

## Observed results

Both retained snapshots below are the **classic 32-assertion population**.
Neither includes the twenty-six challenge assertions, whose Bifrost and CodeQL
evidence is deferred to the v0.4.0 re-run for the freeze reason recorded in the
[challenge-tier expansion](#challenge-tier-expansion) section. They are not
expanded-core numbers and must not be read as any. The Semgrep CE run over the
expanded 58 is reported in that section instead.

The two snapshots are separate populations and are not pooled with each other or
with any other language.

### CodeQL, `reports/codeql-go-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/go-all@7.2.3` from the committed lock, extracting through
go1.26.0. Configuration hash
`56f44b3d983f7ea1dc2fa77a796ac547b01d12535a124f0c9975d3d0b7989161`.

32 results: 16 `reached` and 16 `not-reached`, with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes. 26 of 32 match the expected polarity.
The six mismatches are:

- false negatives: `dfb-taint-go-alias-propagation-positive`,
  `dfb-taint-go-exception-catch-positive`, and
  `dfb-taint-go-expression-positive`;
- false positives: `dfb-taint-go-array-element-negative`,
  `dfb-taint-go-infeasible-branch-negative`, and
  `dfb-taint-go-loop-carried-negative`.

Five of those six are exactly the mismatch set the Java and C# kernels show on
the same templates with the same CLI: pointer/reference aliasing, the
value-carrying control transfer, and integer arithmetic are missed, while array
elements and loop-carried kills are over-approximated. The sixth,
`dfb-taint-go-infeasible-branch-negative`, is Go-specific: CodeQL's Go taint
tracking reports a flow through an `if false { ... }` body that its Java and C#
counterparts prune. It is reported as observed, not tuned away.

`dfb-taint-go-exception-catch-positive` is the capability evidence the
`panic`/`recover` adaptation anticipates: CodeQL 2.26.3 does not carry the
panicked value to `recover`'s result, so the anchored flow is not found. The
fixture expresses the template correctly and is left unchanged.

All 32 retained raw outputs are SARIF files under
`reports/raw/codeql-go-kernel/`, with zero error files, and normalized
`witness_checkpoints` are empty for every case: the adapter records anchor-backed
flow outcomes and leaves the path evidence in SARIF rather than fabricating
observed witness markers. End-to-end per-case wall clock, including cold
database creation and the traced build, ranged from 6.1 s to 10.2 s (about
3.9 minutes for the population), comfortably inside the 60-second
`execution_budget` the cases share with the other language kernels.

### Bifrost, `reports/bifrost-go-kernel.json`

Bifrost 0.10.5, build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`.
Configuration hash
`3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`; it covers
both `core-go-kernel.rqlp` and the breadth `core-direct.rqlp`, because the frozen
direct pair is evaluated through the policy it declares.

32 results: 5 `reached`, 5 `not-reached`, and 22 `inconclusive`. Five template
pairs are decisive — direct propagation, the local multi-step chain, call-context
separation, and the one-hop and two-hop return relays — and all ten of those
outcomes match the expected polarity: 10 of 10 decisive outcomes, 10 of 32
assertions.

The 22 inconclusive results are capability evidence, never negatives. Twelve
retain `partial_discovery` ("procedure value-flow snapshot for ... is unknown")
and ten retain `capability_incomplete`. Of the ten, eight are the heap pairs
(object separation, same-object field separation, alias propagation, array
element), each diagnosed "procedure value-flow snapshot ... is unsupported
(assignments)", and two are the exception-catch pair, diagnosed "taint semantic
binding is unavailable: selected call has no argument at index 0" — Bifrost
cannot bind the sink operand that `recover()` supplies. That is the second
recorded instance of the capability evidence the `panic`/`recover` adaptation
anticipates, and it is reported as an incomplete analysis rather than as a
passing negative.

## Population boundaries

Go results are their own population. They are never pooled with the Java,
JavaScript, TypeScript, Python, Kotlin, or C# kernels, never pooled with the
13-language direct-flow breadth slice, and never averaged with a language whose
core denominator is not the same. Go's expanded core is 29 templates; the
classic snapshots retained above are 16-template numbers and are never compared
to a 29-template one. The Java calibration cases
(`dfb-template-one-hop-relay` and `dfb-template-modeled-external-summary`) have
no Go member and do not change this denominator.

# Ruby propagation kernel

Issue #39 ports the sixteen scored propagation templates to Ruby.
[`docs/applicability-matrix.md`](applicability-matrix.md) fixes the
classifications before any fixture is written, and this contract records the
adaptation each cell actually uses. The `template_id` values are stable
benchmark identities: a template is never renamed, split, merged, or silently
dropped because Ruby spells its Java construct differently.

The classic Ruby core denominator was **16 templates / 32 core assertions**.
With the challenge row rolled out it is **29 templates / 58 core assertions** —
the sixteen classic templates plus the thirteen preregistered challenge
templates, all of which
[the challenge-tier preregistration](challenge-tier.md) classifies as directly
applicable to Ruby. The 16-template v0.3.0 core and this expanded core are
**different populations and are never compared number-to-number**.

Ruby is a **tranche-3, analyzer-coverage-gated** language. The gate and its
resolution are recorded in [the analyzer-coverage gate](#the-analyzer-coverage-gate)
below, before any result is quoted.

## Adaptation table

| Stratum | Template ID | Matrix cell | Ruby construct |
| --- | --- | --- | --- |
| Local | `dfb-template-direct-propagation` | direct | The source result is passed straight to the sink. The negative calls the source separately and sinks a literal. |
| Local | `dfb-template-local-overwrite-kill` | direct | A local is either reassigned to itself or overwritten with a literal before the sink. Ruby locals are mutable by default, so no `var`-style adaptation is needed. |
| Local | `dfb-template-local-multi-step-chain` | direct | The source is copied through three local names before the sink. |
| Local | `dfb-template-arithmetic-expression-propagation` | direct | The source participates in `(value * 3) + 7`. The negative computes the same expression and sinks the literal. |
| Calls/returns | `dfb-template-call-context-separation` | direct | One `relay` method is called with a tainted and a clean argument; only the selected call may reach the sink. |
| Calls/returns | `dfb-template-argument-position-separation` | direct | `choose_first(first, second)` returns its first parameter; moving the source between positions changes the expected flow. |
| Calls/returns | `dfb-template-return-relay-one-hop` | direct | The tainted value crosses one method return. |
| Calls/returns | `dfb-template-return-relay-two-hop` | direct | The tainted value crosses two nested method returns. |
| Heap/separation | `dfb-template-object-separation` | direct | Two `Holder` instances share one `attr_accessor` name; only the tainted instance may reach the sink. |
| Heap/separation | `dfb-template-same-object-field-separation` | direct | One `Holder` exposes separate `tainted` and `clean` accessors; reading one must not inherit the other's flow. |
| Heap/separation | `dfb-template-alias-propagation-separation` | direct | `aliased = original` binds a second name to the same object; a separately constructed `Holder` stays distinct. |
| Heap/separation | `dfb-template-array-element-separation` | direct | A two-element `Array` with constant indices `0` and `1`. Ruby arrays are integer-indexed sequences, so this is direct, not the key-based adaptation PHP needs. |
| Control transfer | `dfb-template-infeasible-branch` | direct | `if false` guards the tainted assignment; the positive uses `if true`. |
| Control transfer | `dfb-template-branch-join` | direct | The source survives a one-armed `if`; overwriting it in both arms produces the negative. |
| Control transfer | `dfb-template-loop-carried-kill` | direct | A counted `while` loop either carries the source through its own update or overwrites it each iteration. |
| Control transfer | `dfb-template-exception-catch` | **adapted (surface form only)** | `raise`/`rescue` with a `StandardError` subclass carrying an `attr_accessor` attribute. |

### The exception-catch adaptation

The matrix classifies this cell as `language-adapted`, and the adaptation is a
**surface-form rename only**. Ruby's `raise`/`rescue` with a `StandardError`
subclass is the same construct as Java's `throw`/`catch` with a checked
exception class: a typed heap object carrying a value crosses a non-local
control transfer and is read out of the handler-bound variable. Nothing about
the flow question changes — only the keywords and the root class do. The
fixture is:

```ruby
class FlowError < StandardError
  attr_accessor :value
end
```

with `flow.value = dfb_source` (positive) or `flow.value = "clean"` (negative)
before `raise flow`, and `dfb_sink(caught.value)` inside
`rescue FlowError => caught`. `StandardError` — not `Exception` — is the
idiomatic Ruby base for an application error and the class a bare `rescue`
would catch; the fixture still names the class explicitly so the handler is an
exact match rather than a catch-all.

This is a surface adaptation, not a semantic substitution like Go's
`panic`/`recover`. If a pinned analyzer cannot prove the transfer, that is
capability evidence — `inconclusive` — and never a redesign of the case into a
construct the tool happens to handle.

### The heap stratum

All four heap templates use ordinary Ruby objects with `attr_accessor`
declarations and post-construction assignment:

```ruby
class Holder
  attr_accessor :value

  def initialize
    @value = "clean"
  end
end
```

`attr_accessor` is the idiomatic Ruby spelling of a public field: it defines a
`value` reader and a `value=` writer over the `@value` instance variable, so
`holder.value = x` is a method call and `holder.value` is another. That is a
real property of Ruby's object model, and it is what the heap fixtures ask the
analyzers about — a tool that models only direct instance-variable access and
not the generated accessor pair will find nothing, and that outcome is
capability evidence rather than a benchmark defect. No global registry, no
`OpenStruct`, no `method_missing`, and no metaprogramming appears in any
fixture.

Alias propagation relies on Ruby assignment binding a second name to the *same*
object; the alias variable is named `aliased` because `alias` is a Ruby
keyword. Object identity, not equal contents, is the distinction under test.

### Arrays

`dfb-template-array-element-separation` uses a fixed two-element array literal
with constant indices, which the matrix classifies as direct. Ruby's `Array` is
an integer-indexed sequence, so index `0` and index `1` are the direct
equivalent of the Java array elements. No slicing, growth, `Hash`, or
enumerable method appears; those would add unrelated semantics.

### Loops and locals

The loop pair uses a counted `while` over an explicit integer counter rather
than `3.times do |i| ... end`. A block would introduce a closure and change the
question from "does the loop carry or kill the value" to "does the analyzer
model block capture", which is a different template. `while` is a direct
spelling of the Java `for` loop, so the cell stays `direct`.

Ruby locals are mutable by default, so `dfb-template-local-overwrite-kill` and
`dfb-template-loop-carried-kill` need none of the `var`/`let mut` adaptation
Kotlin, Scala, and Rust require.

### Parenless calls

Ruby's receiverless zero-argument calls are spelled without parentheses
(`value = dfb_source`), which is both idiomatic and the spelling the frozen
direct-flow breadth fixture already uses. Every *sink* call takes one
positional argument and is spelled with parentheses (`dfb_sink(value)`). That
split matters to anchor reconciliation and is recorded in
[anchor evidence](#anchor-evidence-and-result-semantics) below.

## The 13 challenge templates

[The challenge-tier preregistration](challenge-tier.md) fixed thirteen further
templates — semantic intent, positive and negative shapes, negative mechanisms,
capability kinds, feature tags, and per-language applicability — before any Ruby
challenge fixture existed. The preregistration classifies **all thirteen as
directly applicable to Ruby**, so the expanded Ruby core is **29 templates and
58 assertions**.

Every challenge case carries `score_tier: "core"`,
`model_profile: "benchmark-controlled"`, and fixture provenance revision
`m3-challenge-ruby`. Every fixture is standard library only — `public_send`,
`instance_variable_set`/`instance_variable_get`, `Hash`, `Array`, lambdas,
`method(:name)`, `Class.new`, and plain classes with `attr_accessor`. Nothing
is `require`d, and no gem appears anywhere.

| Stratum | Template ID | Ruby shape and distinction |
| --- | --- | --- |
| A — dispatch/reflection | `dfb-template-chal-reflective-invocation` | `target.public_send(name, dfb_source)` with `name` bound to a local string constant. The negative binds `name` to the sibling `drop`, which sinks a clean constant. |
| A | `dfb-template-chal-computed-property` | `holder.instance_variable_set(key, dfb_source)` then `holder.instance_variable_get(key)` with the same local key variable. The negative writes under `"@alpha"` and reads under the distinct constant `"@beta"`. |
| A | `dfb-template-chal-dispatch-table` | A `Hash` of two lambdas; `table[key].call(dfb_source)`. The negative selects the argument-dropping entry. |
| B — higher-order | `dfb-template-chal-closure-capture` | A lambda closes over `make_reporter`'s tainted local and is returned and `call`ed after that scope has exited. The negative captures a clean local instead. |
| B | `dfb-template-chal-function-field` | `method(:leak)` is stored in `holder.fn` and a separate `dispatch(holder, value)` reads the accessor and `call`s it. The negative dispatches through a second holder whose field holds `method(:drop)`. |
| B | `dfb-template-chal-callback-registration` | A `Registry` instance holds an array of callables; `fire(value)` iterates with `each` and invokes them, unaware of what was registered. The negative registers a callback that ignores its parameter. |
| B | `dfb-template-chal-anonymous-implementation` | Two `Class.new do ... end` anonymous classes each define `handle`; one is instantiated inline and invoked through a local reference. The negative invokes the argument-dropping one. Neither captures anything. |
| C — containers/paths | `dfb-template-chal-map-iteration` | The tainted value is stored under one `Hash` key and retrieved by `records.each do |key, value|`, never by `[]`. The negative iterates a second, disjoint `Hash`. |
| C | `dfb-template-chal-nested-access-path` | A depth-3 accessor chain, `outer.middle.inner.value`, written and read at the identical path. The negative reads the sibling `outer.middle.inner.other`. |
| C | `dfb-template-chal-element-object` | A two-element `Array` of instances; the tainted value sits in `items[0].value`. The negative reads `items[1].value`. |
| D — context/depth | `dfb-template-chal-deep-relay-chain` | Six top-level relays, `relay1` … `relay6`, no branching and no state. The negative feeds the identical chain the clean value. |
| D | `dfb-template-chal-recursive-carry` | `carry(value, depth)` recurses to a constant depth of 5 and returns the carried value at the base case. The negative's base case returns a clean constant instead. |
| D | `dfb-template-chal-context-pair-depth2` | `outer_tainted` and `outer_clean` both reach the *same* `wrapper` and the *same* `helper`; `run` sinks one of the two results. The negative sinks the clean context's result. |

### Ruby adaptations for the challenge tier

Ruby is one of the languages the preregistration classifies `direct` in every
cell, so there is no semantic substitution to record. What *is* recorded here,
before the fixtures were authored, is which of Ruby's several spellings of each
construct the fixtures use, because Ruby usually offers more than one and the
choice changes what the analyzers are asked:

- **`public_send`, not `send`.** Both resolve a method from a run-time string;
  `public_send` refuses private methods, which is the closer analogue of
  `Method#invoke` on a public method and of `getattr` on a public attribute.
  The preregistration's Ruby paragraph names `public_send`, and the fixture
  uses it.
- **`instance_variable_set`/`instance_variable_get`, not a `Hash`.** The
  preregistration's Ruby cell names the instance-variable pair, which preserves
  the *member-access* flavor of the template that C++ and Rust have to give up.
  The keys are `"@alpha"` and `"@beta"` because that is the instance-variable
  spelling those methods take.
- **`method(:name)` for the code-valued field and the registry.** Templates 5
  and 6 need a first-class callable that is *not* an anonymous function, so
  that they stay distinct from templates 4 and 7. `method(:leak)` returns a
  stdlib `Method` object that answers `call`, which is Ruby's ordinary way to
  pass a named method as a value.
- **`Class.new do ... end` for template 7.** Ruby has genuinely anonymous
  classes, so the cell needs no adaptation. Both anonymous classes in the
  fixture are capture-less, which is what keeps template 7 distinct from
  template 4's capture question.
- **`Hash#each` for template 8.** The value is never retrieved with `[]`; the
  block parameters are the only path from the container to the sink.
- **`dfb-template-chal-context-pair-depth2` sinks in the caller**, per
  [Amendment A1](challenge-tier.md#amendments). Both outer contexts stay live
  in one fixture, the shared `helper` returns its parameter, the shared
  `wrapper` returns `helper`'s result, and `run` sinks one of the two outer
  results. This is the k = 2 extension of the classic
  `dfb-template-call-context-separation` fixture, which spells the k = 1 case
  the same way.

The classic Ruby rules above tell fixture authors to keep blocks,
metaprogramming, and `method_missing` out of the sixteen-template core, where
they would substitute for a template that asks a simpler question. That
instruction scopes the classic core only. The challenge tier exists to ask
about dispatch, capture, containers, and depth, and its fixtures use the
constructs deliberately — still with no `method_missing`, no `OpenStruct`, no
`eval`, and no global registry.

Every challenge fixture is `Syntax OK` under the same system Ruby the classic
fixtures use (`/usr/bin/ruby -c`, `ruby 2.6.10p210`). No adapter compiles or
executes them.

## Fixtures

Fixtures are single `.rb` files with no `require`, no gem, no module nesting,
and no external dependency. They use the benchmark-controlled `dfb_source` and
`dfb_sink` endpoint names in Ruby's snake_case — the same spelling the
cross-language contract already uses — with `DFB-SOURCE:` and `DFB-SINK:`
marker comments on the endpoint declaration lines. Every fixture parses under
the system Ruby (`/usr/bin/ruby`, `ruby 2.6.10p210`, `ruby -c`). No adapter
compiles or executes them.

## Case population and the frozen direct pair

The Ruby core population is the 58 `taint`/`core` cases under
`cases/taint/ruby/`. Thirty of them were authored for the classic kernel with
`fixture_provenance.revision` `m2-ruby-kernel`, and twenty-six for the
challenge tier with revision `m3-challenge-ruby`. The direct-propagation pair
(`dfb-taint-ruby-direct-positive` and `dfb-taint-ruby-direct-negative`)
predates it: it is the Ruby member of the 13-language direct-flow breadth
slice, and it is frozen byte-for-byte in the published manifest
(`reports/freeze.json`). Its `case.json` therefore keeps
`fixture_provenance.revision` `m1a-direct-core`, keeps the breadth policy
reference `adapters/bifrost/policies/core-direct.rqlp`, and carries no CodeQL
model reference.

Editing those two files would invalidate published evidence, so the runners
accommodate them instead, exactly as the [Kotlin](kotlin-kernel.md),
[C#](csharp-kernel.md), [Go](go-kernel.md), and [Rust](rust-kernel.md) kernels
do:

- the Bifrost Ruby selector accepts either `core-ruby-kernel.rqlp` or the
  breadth `core-direct.rqlp` policy for a Ruby case, and evaluates each case
  through the policy it declares;
- the CodeQL Ruby selector defaults a Ruby case with no `codeql` model
  reference to this kernel's query, and rejects any Ruby case that names a
  different query.

The same case is a member of two populations, but its results are never pooled:
the breadth result lives in `reports/bifrost-smoke.json` and the kernel results
in the dedicated Ruby reports below.

## The analyzer-coverage gate

`docs/applicability-matrix.md` gates this tranche explicitly: Bifrost is
`inconclusive` for **both** Ruby direct assertions in the frozen breadth smoke,
so the Ruby tranche either waits for Bifrost's Ruby indexing to be fixed, or
proceeds CodeQL-first with the Bifrost outcomes retained as inconclusive
capability evidence.

**The decision recorded here is: proceed CodeQL-first.** Concretely:

1. **CodeQL is the primary decisive analyzer** for the Ruby denominator. The
   pinned CLI 2.26.3 ships a production `ruby` extractor and the registry
   resolves `codeql/ruby-all@6.0.3`, so every assertion in the denominator can
   be decided by a real, reproducible toolchain.
2. **Bifrost is run anyway** on the full population through
   `core-ruby-kernel.rqlp`, and whatever it produces is retained verbatim as
   capability evidence. Bifrost's Ruby indexing was *not* changed as part of
   this tranche; that work belongs to Bifrost, not to the benchmark.
3. **No Bifrost outcome is converted into a negative.** An `inconclusive`
   Bifrost result is capability coverage. It never counts as `not-reached`,
   never enters the negative half of a scorecard, and never suppresses the
   CodeQL result for the same assertion.
4. **Joern is run as a second decisive analyzer** through `rubysrc2cpg`, which
   the pinned distribution ships. Its population, report, and evidence root are
   separate from CodeQL's and from Bifrost's.

The gate is about *coverage*, not about polarity: it changes which analyzer the
Ruby denominator is decided by, and it changes nothing about the fixtures, the
template identities, or the expected polarities.

## Bifrost selection and reproduction

The Bifrost Ruby slice uses the language-qualified policy
`adapters/bifrost/policies/core-ruby-kernel.rqlp`, whose source and sink
selectors are `(language ruby (call :callee (name "dfb_source")))` and
`(language ruby (call :callee (name "dfb_sink")))`, with argument index 0 as
the dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-ruby-kernel --bifrost /path/to/bifrost
```

The command selects exactly the 58 Ruby core assertions, materializes one
isolated workspace per case outside the repository, writes the normalized
report to `reports/bifrost-ruby-kernel.json`, and retains the verbatim per-case
Bifrost JSON under `reports/raw/bifrost-ruby-kernel/`. A report with incomplete
runs is normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

Ruby has its own CodeQL pack at `adapters/codeql/ruby/`, with its own
`qlpack.yml`, its own `codeql-pack.lock.yml`, and `queries/RubyKernel.ql`. It
does not share the Java, Python, or any other language pack.

| Item | Value |
| --- | --- |
| CLI | 2.26.3 (pinned) |
| Extractor | `ruby`, buildless (`--build-mode=none`) |
| Library pack | `codeql/ruby-all@6.0.3` |
| Pack | `adapters/codeql/ruby` |
| Query | `adapters/codeql/ruby/queries/RubyKernel.ql` |

The query is the same minimal, language-neutral contract every other kernel
query implements: sources are calls whose method name is `dfb_source`, sinks
are the first positional argument of calls whose method name is `dfb_sink`, and
the body is one `TaintTracking::Global` configuration. There is no per-case,
per-template, or per-polarity branching. Ruby's parenless call surface is
irrelevant to the query — a receiverless `dfb_source` is the same `MethodCall`
node as `dfb_source()`.

Reproduce with:

```bash
codeql pack install adapters/codeql/ruby
cargo run -- run-codeql-ruby-kernel --codeql /path/to/codeql
```

`codeql pack install` resolved `codeql/ruby-all@6.0.3` from the registry
directly, so this pack needs none of the `--codeql-packs` source-workspace
fallback [the JavaScript kernel](javascript-kernel.md) documents.

The runner creates one **cold** database per case from a workspace holding only
that case's fixture file, runs the kernel query, reconciles the SARIF against
the case's own anchors, retains the complete SARIF under
`reports/raw/codeql-ruby-kernel/`, and writes the dedicated normalized report to
`reports/codeql-ruby-kernel.json`.

## Joern selection and reproduction

The Ruby Joern kernel uses the shared script
`adapters/joern/queries/kernel.sc` with the `RUBYSRC` frontend
(`rubysrc2cpg`), exactly as the Java, JavaScript, and Python kernels use their
own frontends. Nothing in the script is language-specific; the two
benchmark-controlled endpoint identifiers are read out of each fixture's
`DFB-SOURCE:` and `DFB-SINK:` marker lines and passed in as parameters.

```bash
cargo run -- run-joern-ruby-kernel --joern <joern-cli>/joern
```

The runner selects the 58 Ruby core assertions, builds one cold CPG per case in
a per-case scratch root, retains the evidence document under
`reports/raw/joern-ruby-kernel/`, and writes
`reports/joern-ruby-kernel.json`. A frontend or engine failure is retained as
`runner-error` and can never become a negative.

## Semgrep CE selection and reproduction

The Ruby Semgrep slice uses the committed rule
`adapters/semgrep/rules/ruby.yaml`. It is the one rule file that differs in
substance from the other ten: a Ruby call's parameter list is optional and every
Ruby fixture spells the source call parenless (`value = dfb_source`), so its
`pattern-sources` is a `pattern-either` over both spellings, while the sink keeps
the single parenthesised form every language uses.

```bash
cargo run -- run-semgrep-ruby-kernel --semgrep /path/to/semgrep
```

The runner selects all 58 Ruby core assertions, scores the 14 that fall inside
the bounded CE profile, and normalizes the other 44 `unsupported` **without
invoking Semgrep** — the decision is taken from the case's own
`feature_tags` and `expected_analysis_capability`, and for a challenge template
from the preregistered `CHALLENGE_SEMGREP_PARTITION`, before the tool runs. The
partition is not adjustable by a result.

## Anchor evidence and result semantics

Analyzer findings are evidence, not ground truth by themselves. The runners
reconcile finding locations against the case's `DFB-SINK:` anchor: the marker
identifies the sink function's declaration, and a finding is accepted when it
lies in the same fixture file on a line that *calls* that function. The finding
need not be on the marker's own line.

Ruby needs its own dialect in the shared reconciler for two surface reasons,
both derived from the fixtures themselves rather than assumed:

1. **The parameter list is optional.** `def dfb_source # DFB-SOURCE: ...`
   declares a method just as `def dfb_sink(value) # DFB-SINK: ...` does, so the
   declared name is read *after* the `def` keyword rather than *before* a
   parameter list. Every other dialect reconciled here can rely on the
   parameter list; Ruby cannot. This matters most for Joern, which resolves the
   source endpoint name from the source marker line — a parameter-list rule
   would have failed to resolve it and the case would have been reported as
   inconclusive rather than analyzed.
2. **Comments open with `#`, and members are reached through `.` and `::`.**
   Ruby shares the `#` comment opener with Python and the `::` path separator
   with Rust, but no existing dialect combines both, so `AnchorDialect::Ruby`
   pairs `CommentSyntax::Hash` with the `['.', ':']` member prefixes.

A parenless call is deliberately *not* treated as a sink callsite: every
benchmark sink takes one positional argument and every fixture spells that call
with parentheses, while the parenless calls that do appear are all source
calls, whose names are resolved from declaration lines rather than by scanning
for callsites.

A successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing, ambiguous, or unmappable location
evidence is `inconclusive`, an explicitly unsupported capability is
`unsupported`, and a database, query, SARIF, process, or runner failure is
`runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This is exactly
what keeps the Bifrost coverage gate honest.

## Which adapters ran, and which are deferred

Four adapters cover Ruby, and **all four ran over the whole expanded
58-assertion population** in this wave. Nothing about Ruby is deferred.

| Adapter | Expanded-population run | Report | Freeze-bound? |
| --- | --- | --- | --- |
| CodeQL CLI 2.26.3 (`ruby`) | **Ran** — whole 58-assertion population | `reports/codeql-ruby-kernel.json` | No |
| Joern 4.0.610 (`rubysrc2cpg`) | **Ran** — whole 58-assertion population | `reports/joern-ruby-kernel.json` | No |
| Bifrost v0.10.5 | **Ran** — whole 58-assertion population | `reports/bifrost-ruby-kernel.json` | No |
| Semgrep CE 1.174.0 | **Ran** — whole 58-assertion population | `reports/semgrep-ruby-kernel.json` | No |

This is the one difference between the Ruby wave and the earlier ones. The
v0.3.0 freeze manifest (`reports/freeze.json`) digest-binds nineteen reports —
the Bifrost smoke report, eight Bifrost kernel reports, and the ten CodeQL
kernel reports of the ten languages frozen in v0.3.0. Ruby's kernel landed
*after* that freeze, so **no Ruby report is in the manifest's report list**,
and each of the four could be replaced whole without touching published
evidence. `validate-freeze` passes on the resulting tree, which is the check
that proves it rather than the claim that asserts it.

Every Ruby report is a **whole-population replacement**, never an append: each
of the four was re-run over all 58 assertions and now carries fixture revision
`sha256:020d0d8f79360af6e74064a692e2d65ffa31cd97f9971f9dad8bec065d862043`, the
expanded corpus. Ruby's challenge cases are excluded from the Bifrost *smoke*
selection, which stays pinned at its frozen 118 cases.

## Observed results

All four snapshots cover the same 58 Ruby core assertions and are four
separate populations. They are never merged into one Ruby number, and the
58-assertion expanded core is never compared number-to-number with the
32-assertion v0.3.0 core.

| Analyzer | `reached` | `not-reached` | `unsupported` | `inconclusive` | `runner-error` | Polarity match |
| --- | --- | --- | --- | --- | --- | --- |
| CodeQL 2.26.3 | 22 | 36 | 0 | 0 | 0 | **49/58** (49 of 58 decisive) |
| Joern 4.0.610 | 23 | 35 | 0 | 0 | 0 | **40/58** (40 of 58 decisive) |
| Semgrep CE 1.174.0 | 9 | 5 | 44 | 0 | 0 | 12/14 scored |
| Bifrost v0.10.5 | 0 | 0 | 0 | 58 | 0 | 0/58 (0 decisive) |

Per-stratum, for the two whole-population decisive analyzers:

| Stratum | Assertions | CodeQL | Joern |
| --- | --- | --- | --- |
| Classic (16 templates) | 32 | 29/32 | 26/32 |
| A — dispatch and reflection | 6 | 3/6 | 3/6 |
| B — higher-order flow | 8 | 5/8 | 4/8 |
| C — containers and deep access paths | 6 | **6/6** | 3/6 |
| D — context and depth stress | 6 | **6/6** | 4/6 |
| **Expanded core** | **58** | **49/58** | **40/58** |

Both classic columns reproduce the previous 16-template runs case for case —
the same 29/32 for CodeQL and the same 26/32 for Joern, with the same mismatch
sets — so the expansion disturbed no existing evidence.

### CodeQL, `reports/codeql-ruby-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/ruby-all@6.0.3` from the committed lock. Configuration hash
`0292361f24c7b18fa59543de15e5709270a5d717f0e7fa3e61de7a9436fb59f7` — unchanged,
because neither the query nor the pack moved; only the population grew.

All 58 assertions executed cleanly: 22 `reached`, 36 `not-reached`, and zero
`inconclusive`, `unsupported`, or `runner-error` outcomes. Every one of the 58
raw outputs is a SARIF document under `reports/raw/codeql-ruby-kernel/`; there
are zero retained error files. The population ran in 468 s wall clock, 5.7 s to
14.5 s per case.

**49 of 58** outcomes match the expected polarity. The three classic mismatches
are unchanged:

- `dfb-taint-ruby-alias-propagation-positive`: false negative — writing through
  `original.value` and reading through `aliased.value` is not carried across
  the alias.
- `dfb-taint-ruby-exception-catch-positive`: false negative — the value stored
  on the `FlowError` attribute is not carried through `raise`/`rescue` to
  `caught.value`.
- `dfb-taint-ruby-loop-carried-negative`: false positive — the `while` body
  overwrites the local on every iteration, and the kill is not proven.

The six challenge mismatches, verbatim:

- `dfb-taint-ruby-reflective-invocation-positive`: false negative.
- `dfb-taint-ruby-computed-property-positive`: false negative.
- `dfb-taint-ruby-dispatch-table-positive`: false negative.
- `dfb-taint-ruby-function-field-positive`: false negative.
- `dfb-taint-ruby-callback-registration-positive`: false negative.
- `dfb-taint-ruby-anonymous-implementation-positive`: false negative.

Read as the preregistration requires:

- **Stratum A is approximation character, not skill, and CodeQL's character
  here is uniformly under-approximating.** All six stratum-A results are
  `not-reached`: the three positives are false negatives and the three
  negatives are correct for the same reason the positives are wrong. A callee
  named by `public_send`, a member located by
  `instance_variable_set`/`instance_variable_get`, and a lambda fetched from a
  `Hash` are all declined. 3/6 here is *not* "half right"; it is one
  consistent design position scored twice, and it does not rank CodeQL against
  anything.
- **Stratum B separates the four difficulties, which is why it was split into
  four.** Environment capture (`closure-capture`) is the one cell CodeQL
  decides on both halves — the lambda closing over `make_reporter`'s local is
  followed out of the creating scope. Code stored in a field
  (`function-field`), inversion of control (`callback-registration`), and the
  anonymous `Class.new` implementation are all missed on the positive.
  Collapsing these four into one template would have reported "half" and hidden
  which half.
- **Stratum C is fully decided**, including the depth-3 accessor chain and the
  element-plus-field pair, and including `Hash#each` iteration. Read against
  the classic `same-object-field-separation` and `array-element-separation`
  results, this says Ruby field sensitivity here is not k-limited at depth 1 or
  2, and that the map is modeled through its iteration protocol and not only
  through `[]`.
- **Stratum D is fully decided**, six-hop relay included. The preregistration's
  depth calibration was aimed at Joern's verified `maxCallDepth = 4`; it says
  nothing about CodeQL's bound, and CodeQL's Ruby analysis resolves the chain,
  the depth-5 recursion, and the k = 2 context pair.

### Joern, `reports/joern-ruby-kernel.json`

Joern 4.0.610, build identity `joern-cli:4.0.610`, frontend `rubysrc2cpg`.
Configuration hash
`ab10e81860305e492a930e2c2691873b23be25e97e5b354ca785058e09a20025` — the shared
`adapters/joern/queries/kernel.sc` was not modified, so the hash is unchanged.

All 58 assertions executed: 23 `reached`, 35 `not-reached`, and zero
`inconclusive`, `unsupported`, or `runner-error` outcomes. **40 of 58** match
the expected polarity. The six classic mismatches are unchanged from the
16-template run:

- `dfb-taint-ruby-alias-propagation-positive`: false negative.
- `dfb-taint-ruby-exception-catch-positive`: false negative.
- `dfb-taint-ruby-argument-position-negative`: false positive.
- `dfb-taint-ruby-call-context-negative`: false positive.
- `dfb-taint-ruby-infeasible-branch-negative`: false positive.
- `dfb-taint-ruby-loop-carried-negative`: false positive.

The twelve challenge mismatches, verbatim:

- `dfb-taint-ruby-reflective-invocation-positive`: false negative.
- `dfb-taint-ruby-computed-property-negative`: false positive.
- `dfb-taint-ruby-dispatch-table-positive`: false negative.
- `dfb-taint-ruby-closure-capture-positive`: false negative.
- `dfb-taint-ruby-function-field-positive`: false negative.
- `dfb-taint-ruby-callback-registration-positive`: false negative.
- `dfb-taint-ruby-anonymous-implementation-positive`: false negative.
- `dfb-taint-ruby-map-iteration-positive`: false negative.
- `dfb-taint-ruby-nested-access-path-positive`: false negative.
- `dfb-taint-ruby-element-object-positive`: false negative.
- `dfb-taint-ruby-context-pair-depth2-positive`: false negative.
- `dfb-taint-ruby-recursive-carry-negative`: false positive.

Read as the preregistration requires:

- **Stratum A shows both propensities in one engine.** `rubysrc2cpg` declines
  the `public_send` callee and the `Hash`-selected lambda — under-approximating,
  missing both positives and declining both negatives for the same reason. On
  `computed-property` it does the opposite: it carries the value through the
  `instance_variable_set`/`instance_variable_get` pair *and* joins the two
  provably distinct constant keys, so the positive is right and the negative is
  a false positive. That is approximation character, not a ranking.
- **Stratum B is 4/8 and every miss is a positive.** All eight results are
  `not-reached`: no callee reached through a lambda, a `Method` object in an
  accessor, an array of registered callables, or an anonymous `Class.new`
  instance is resolved, so the four negatives are correct for the same reason
  the four positives are wrong. Joern's Ruby stratum B is a clean
  under-approximation, and unlike CodeQL it does not carry closure capture
  either.
- **Stratum C is 3/6, and all six results are `not-reached`.** Iteration over a
  `Hash`, a depth-3 accessor chain, and a field inside an array element are all
  declined on the positive. Read against the classic heap stratum — where
  `rubysrc2cpg` decides `same-object-field-separation` and
  `array-element-separation` correctly — this says the depth-1 field
  sensitivity the classic core establishes does not extend to depth 3, to
  container iteration, or to element-scoped fields.
- **Stratum D contradicts the preregistration's depth prediction for this
  language, and is recorded as such.** `docs/challenge-tier.md` predicts that a
  six-hop relay, calibrated past Joern's verified `maxCallDepth = 4` default,
  will fall off. The adapter did not raise that bound, and on Ruby the relay
  positive is nevertheless `reached` while its negative is `not-reached` — a
  correctly discriminated pair at depth 6. The recursion positive is `reached`
  too, but so is its `overwrite-kill` negative: the recursive summary is
  widened to "everything in, everything out", which is exactly the widening
  template 12's negative exists to make visible. The k = 2 context pair is
  `not-reached` on both halves, so its negative is a true negative arrived at
  by not seeing that far. The prediction is left in the preregistration
  unamended: it was made about the engine's default bound and one language's
  frontend result does not retroactively change what was predicted.

Joern and CodeQL agree on the two classic false negatives — alias propagation
and exception catch — and on the loop-carried false positive; Joern
additionally over-approximates argument-position separation, call-context
separation, and the infeasible branch. On the challenge tier they agree on five
of the six CodeQL misses (`reflective-invocation`, `dispatch-table`,
`function-field`, `callback-registration`, `anonymous-implementation`), and
diverge on `computed-property` — CodeQL declines both halves, Joern resolves
both halves — and on `closure-capture`, stratum C, and stratum D, which CodeQL
decides and Joern does not.

#### Drift between the two Joern pins

This concerns the classic stratum only; no challenge fixture existed under
either earlier pin. On the 16-template core the `4.0.610` numbers replaced a
`4.0.432` run that also scored **26/32** with an also-18/14 outcome
distribution — but with a *different* mismatch set. Re-pinning to `4.0.610`
moved four Ruby cases, two in each direction:

- `dfb-taint-ruby-array-element-negative`: false positive → correct
  `not-reached`.
- `dfb-taint-ruby-same-object-field-negative`: false positive → correct
  `not-reached`.
- `dfb-taint-ruby-argument-position-negative`: correct `not-reached` → false
  positive.
- `dfb-taint-ruby-call-context-negative`: correct `not-reached` → false
  positive.

Under `4.0.432` Ruby's mismatch set was identical to JavaScript's; it no longer
is. `rubysrc2cpg` gained array-element and same-object-field separation and lost
argument-position and call-context separation. Nothing in this benchmark changed
between the two runs but the pinned Joern version, and the raw evidence for all
four cases shows both endpoints observed with the flow count moving in the
direction the outcome reports — so this is analyzer drift, retained as a result.

#### Reaching the Ruby frontend at all

Joern ships `rubysrc2cpg` and its console reports `importCode.ruby` as
available, but the *generic* `importCode(language = "RUBYSRC")` dispatcher the
shared kernel script used has no Ruby entry: it raises
`io.joern.console.ConsoleException: No CPG generator exists for language:
RUBYSRC` for every case, in every spelling of the identifier, and the first
Ruby run produced 32 `runner-error` results because of it. The named
`importCode.ruby` frontend reaches the same generator in the same console, so
`adapters/joern/queries/kernel.sc` now dispatches Ruby through it and leaves
every other language on the generic path unchanged.

That is an adapter fix, not a fixture or query concession: no Ruby fixture was
altered, the query is the same `sinks.reachableByFlows(sources)` every other
Joern kernel runs, and the endpoint identifiers are still read off the
fixtures' own marker lines. Because the shared script's bytes changed, the
other Joern kernels were re-run on the new script so that no retained report
cites a configuration hash its script no longer has.

The workaround was re-probed against `4.0.610` rather than assumed to be
obsolete: the generic dispatcher still raises the same exception for `RUBYSRC`
on that version, so the named-dispatch branch is kept.

### Semgrep CE, `reports/semgrep-ruby-kernel.json`

Semgrep CE 1.174.0, build identity `semgrep-oss:1.174.0`. Configuration hash
`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100` — the
committed rule set was not touched for this tier.

All 58 assertions were selected and balance-checked; **14 were scored and 44
were `unsupported` by declared capability**, decided from the case metadata
before Semgrep was invoked. Zero `inconclusive` and zero `runner-error`
outcomes; 44 retained capability-decision documents, 14 retained finding
documents, 14 retained resolved rule files, and zero error documents under
`reports/raw/semgrep-ruby-kernel/`.

| Partition | Assertions | Outcome |
| --- | --- | --- |
| Scored (`intraprocedural` partition, all classic) | 14 | 9 `reached`, 5 `not-reached`; 12/14 polarity match |
| `unsupported` — rest of the classic core | 18 | capability coverage |
| `unsupported` — challenge strata A, B, C, D | 26 | capability coverage |

**Every one of the 26 challenge assertions took the preregistered
`unsupported` partition**, which is what `docs/challenge-tier.md` said would
happen and is correct behavior for a bounded engine rather than a gap. None of
the thirteen challenge templates carries the `intraprocedural` feature tag, so
none enters the scored subset, and **the scored subset stays at 14** with the
same two mismatches as before — false positives on
`infeasible-branch-negative` and `loop-carried-negative`, the path sensitivity
the pinned CLI documents as Pro-only. The expansion moved the `unsupported`
remainder from 18 to 44 and moved nothing else.

### Bifrost, `reports/bifrost-ruby-kernel.json`

Bifrost v0.10.5, build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`. Configuration hash
`5e57410aee16c7c6f17e9f7645982f035d2561db697deb40e4f57668c34c8cad`.

**All 58 results are `inconclusive`. None is decisive, and none is a
negative.** This is the gate's predicted outcome, now measured over the whole
29-template population rather than only the 16-template core or the two breadth
assertions: the frozen breadth smoke already recorded both Ruby direct
assertions as `inconclusive` under this build, and neither expansion changes
the picture.

The retained per-case evidence under `reports/raw/bifrost-ruby-kernel/` splits
into four groups, counted from the retained documents on this tree:

- **28 `partial_discovery`** — 20 classic (the ten local, call/return, and
  control-transfer pairs) and 8 challenge (`computed-property`,
  `context-pair-depth2`, `deep-relay-chain`, `recursive-carry`). Each retains a
  diagnostic of the form "procedure value-flow snapshot for `<procedure>` is
  unknown".
- **14 `capability_incomplete`, "unsupported (assignments)"** — the four
  classic heap/separation pairs, the classic exception-catch pair, and the
  challenge `nested-access-path` and `element-object` pairs.
- **14 `capability_incomplete`, "taint semantic binding is unavailable: no
  analysis root contains both a selected source and sink"** — the seven
  challenge pairs whose sink call sits inside a lambda, a block, a `Method`
  object, or an anonymous class body: `reflective-invocation`,
  `dispatch-table`, `closure-capture`, `function-field`,
  `callback-registration`, `anonymous-implementation`, and `map-iteration`.
  This diagnostic is new to the challenge tier and is retained as it was
  emitted.
- **2 `capability_incomplete`, "unsupported (local_flow)"** — the classic
  loop-carried pair.

Bifrost's Ruby indexing was deliberately not modified by this wave, any more
than it was by the original tranche. Under
[the gate](#the-analyzer-coverage-gate) these 58 results are retained verbatim
as capability coverage; not one of them is counted as `not-reached`, and the
Ruby denominator is decided by CodeQL instead.

## Population boundaries

Ruby results are their own population. They are never pooled with the Java,
JavaScript, TypeScript, Python, Kotlin, C#, Go, C, C++, or Rust kernels, and
never pooled with the 13-language direct-flow breadth slice. The four Ruby
analyzer populations — CodeQL, Joern, Semgrep CE, and Bifrost — are four
separate result sets over one case population and are never merged into a
single Ruby number. Nor are the 32-assertion v0.3.0 Ruby core and this
58-assertion expanded core: they are two populations of the same name, and a
sentence that subtracts one from the other is a misreading. The Java
calibration cases (`dfb-template-one-hop-relay` and
`dfb-template-modeled-external-summary`) have no Ruby member and do not change
this denominator.

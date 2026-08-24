# Ruby propagation kernel

Issue #39 ports the sixteen scored propagation templates to Ruby.
[`docs/applicability-matrix.md`](applicability-matrix.md) fixes the
classifications before any fixture is written, and this contract records the
adaptation each cell actually uses. The `template_id` values are stable
benchmark identities: a template is never renamed, split, merged, or silently
dropped because Ruby spells its Java construct differently.

The Ruby core denominator is **16 templates / 32 core assertions**, the same as
Kotlin, Scala, C#, Go, PHP, C++, and TypeScript.

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

## Fixtures

Fixtures are single `.rb` files with no `require`, no gem, no module nesting,
and no external dependency. They use the benchmark-controlled `dfb_source` and
`dfb_sink` endpoint names in Ruby's snake_case — the same spelling the
cross-language contract already uses — with `DFB-SOURCE:` and `DFB-SINK:`
marker comments on the endpoint declaration lines. Every fixture parses under
the system Ruby (`/usr/bin/ruby`, `ruby 2.6.10p210`, `ruby -c`). No adapter
compiles or executes them.

## Case population and the frozen direct pair

The Ruby core population is the 32 `taint`/`core` cases under
`cases/taint/ruby/`. Thirty of them were authored for this kernel with
`fixture_provenance.revision` `m2-ruby-kernel`. The direct-propagation pair
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
   resolves `codeql/ruby-all@6.0.3`, so all 32 assertions can be decided by a
   real, reproducible toolchain.
2. **Bifrost is run anyway** on the full 32-assertion population through
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

The command selects exactly the 32 Ruby core assertions, materializes one
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
cargo run -- run-joern-ruby-kernel --joern /usr/local/bin/joern
```

The runner selects the 32 Ruby core assertions, builds one cold CPG per case in
a per-case scratch root, retains the evidence document under
`reports/raw/joern-ruby-kernel/`, and writes
`reports/joern-ruby-kernel.json`. A frontend or engine failure is retained as
`runner-error` and can never become a negative.

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

## Observed results

All three snapshots cover the same 32 Ruby core assertions and are three
separate populations. They are never merged into one Ruby number.

Fixture revision for all three:
`sha256:131ef7e1cc3a22c1cf687770dbb4a1e44dac0456575ed4dad32b5196debaa710`.

| Analyzer | `reached` | `not-reached` | `inconclusive` | `runner-error` | Polarity match |
| --- | --- | --- | --- | --- | --- |
| CodeQL 2.26.3 | 15 | 17 | 0 | 0 | **29/32** (29 of 32 decisive) |
| Bifrost v0.10.5 | 0 | 0 | 32 | 0 | 0/32 (0 decisive) |
| Joern 4.0.432 | 18 | 14 | 0 | 0 | **26/32** (26 of 32 decisive) |

### CodeQL, `reports/codeql-ruby-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/ruby-all@6.0.3` from the committed lock. Configuration hash
`0292361f24c7b18fa59543de15e5709270a5d717f0e7fa3e61de7a9436fb59f7`.

All 32 assertions executed cleanly: 15 `reached`, 17 `not-reached`, and zero
`inconclusive`, `unsupported`, or `runner-error` outcomes. Every one of the 32
raw outputs is a SARIF document under `reports/raw/codeql-ruby-kernel/`; there
are zero retained error files. The population ran in 258 s wall clock, 4.2 s to
11.6 s per case.

**29 of 32** outcomes match the expected polarity. The three mismatches are:

- `dfb-taint-ruby-alias-propagation-positive`: false negative — writing through
  `original.value` and reading through `aliased.value` is not carried across
  the alias.
- `dfb-taint-ruby-exception-catch-positive`: false negative — the value stored
  on the `FlowError` attribute is not carried through `raise`/`rescue` to
  `caught.value`.
- `dfb-taint-ruby-loop-carried-negative`: false positive — the `while` body
  overwrites the local on every iteration, and the kill is not proven.

That is the same mismatch shape the Java, Kotlin, C#, and Python CodeQL kernels
show on those templates, with Ruby additionally getting the arithmetic
expression and array-element pairs right where several other kernels do not.
This is the CodeQL-first evidence the gate names as decisive.

### Bifrost, `reports/bifrost-ruby-kernel.json`

Bifrost v0.10.5, build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`. Configuration hash
`5e57410aee16c7c6f17e9f7645982f035d2561db697deb40e4f57668c34c8cad`.

**All 32 results are `inconclusive`. None is decisive, and none is a
negative.** This is the gate's predicted outcome, now measured over the whole
16-template population rather than only the two breadth assertions: the frozen
breadth smoke already recorded both Ruby direct assertions as `inconclusive`
under this build, and extending the population does not change the picture.

The retained per-case evidence under `reports/raw/bifrost-ruby-kernel/` splits
into two incompleteness reasons:

- **20 `partial_discovery`** — the ten local, call/return, and control-transfer
  pairs. Each retains a diagnostic of the form "procedure value-flow snapshot
  for `<fixture>.run` is unknown".
- **12 `capability_incomplete`** — the four heap/separation pairs plus the
  exception-catch pair ("… is unsupported (assignments)") and the loop-carried
  pair ("… is unsupported (local_flow)").

Bifrost's Ruby indexing was deliberately not modified by this tranche. Under
[the gate](#the-analyzer-coverage-gate) these 32 results are retained verbatim
as capability coverage; not one of them is counted as `not-reached`, and the
Ruby denominator is decided by CodeQL instead.

### Joern, `reports/joern-ruby-kernel.json`

Joern 4.0.432, build identity `joern-cli:4.0.432`, frontend `rubysrc2cpg`.
Configuration hash
`479f676518d0778d2580302ee143f35854c54999b53a1e30fc2781eadf9f082e`.

All 32 assertions executed: 18 `reached`, 14 `not-reached`, and zero
`inconclusive`, `unsupported`, or `runner-error` outcomes. **26 of 32** match
the expected polarity:

- `dfb-taint-ruby-alias-propagation-positive`: false negative.
- `dfb-taint-ruby-exception-catch-positive`: false negative.
- `dfb-taint-ruby-array-element-negative`: false positive.
- `dfb-taint-ruby-infeasible-branch-negative`: false positive.
- `dfb-taint-ruby-loop-carried-negative`: false positive.
- `dfb-taint-ruby-same-object-field-negative`: false positive.

That is the same profile Joern's JavaScript kernel shows, which is what a
shared engine over a dynamic-language frontend should look like. Joern and
CodeQL agree on the two false negatives — alias propagation and exception
catch — and on the loop-carried false positive; Joern additionally
over-approximates array-element separation, same-object field separation, and
the infeasible branch.

#### Reaching the Ruby frontend at all

Joern 4.0.432 ships `rubysrc2cpg` and its console reports `importCode.ruby` as
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
Java, JavaScript, and Python Joern kernels were re-run on the new script so
that no retained report cites a configuration hash its script no longer has.

## Population boundaries

Ruby results are their own population. They are never pooled with the Java,
JavaScript, TypeScript, Python, Kotlin, C#, Go, C, C++, or Rust kernels, and
never pooled with the 13-language direct-flow breadth slice. The three Ruby
analyzer populations — CodeQL, Bifrost, and Joern — are three separate result
sets over one case population and are never merged into a single Ruby number.
The Java calibration cases (`dfb-template-one-hop-relay` and
`dfb-template-modeled-external-summary`) have no Ruby member and do not change
this denominator.

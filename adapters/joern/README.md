# Joern adapter

The Joern adapter runs the Java, JavaScript, Python, Ruby, PHP, and Rust
propagation kernels through Joern's source frontends and its OSS data-flow
engine. Each language is its own population: its own case selection, its own
frontend, its own normalized report, and its own retained-evidence directory.
Joern shares one CPG query language and one data-flow engine across all six,
exactly as CodeQL shares a standard library across its packs; the populations
are kept apart by the selector and the report paths, never by the engine.

PHP is the one language here for which Joern is not a third opinion: the pinned
CodeQL CLI has no PHP support at all, so Bifrost and Joern are PHP's only two
whole-population analyzers, alongside the deliberately bounded Semgrep CE
adapter, which scores only PHP's 14-assertion intraprocedural partition. PHP's
challenge-tier row is rolled out, so this kernel's denominator is the expanded
29 templates / 58 assertions. See [the PHP kernel
contract](../../docs/php-kernel.md).

## Pinned distribution

| Item | Value |
| --- | --- |
| Version | `4.0.610` (the version the console banner reports) |
| Build identity | `joern-cli:4.0.610` |
| Installation | `joern-cli/joern` from the released `joern-cli` distribution |
| Query script | `adapters/joern/queries/kernel.sc` |
| Configuration hash | `ab10e81860305e492a930e2c2691873b23be25e97e5b354ca785058e09a20025` |

The pinned distribution reports no build SHA separate from its released
version, so the released version *is* the build identity. That is recorded
literally rather than padded with a synthetic identifier.

The runner takes the binary as a flag rather than a hard-coded path, so the
distribution can live anywhere; the pin recorded here is the *version*, and
every retained Joern report carries it as `tool_version`. The pin moved from
`4.0.432` to `4.0.610` to pick up `rust2cpg`, which does not exist in the older
release. All six kernels — not only Rust — were re-run on `4.0.610`, so every
retained Joern report cites one tool version and one configuration hash.

## Invocation

Substitute the path of the pinned distribution's `joern` binary:

```bash
cargo run -- run-joern-java-kernel       --joern <joern-cli>/joern
cargo run -- run-joern-javascript-kernel --joern <joern-cli>/joern
cargo run -- run-joern-python-kernel     --joern <joern-cli>/joern
cargo run -- run-joern-ruby-kernel       --joern <joern-cli>/joern
cargo run -- run-joern-php-kernel        --joern <joern-cli>/joern
cargo run -- run-joern-rust-kernel       --joern <joern-cli>/joern
```

`php2cpg` shells out to its bundled PHP-Parser
(`frontends/php2cpg/bin/php-parser/php-parser-4.15.10.phar`), which is itself a
PHP program, so the PHP kernel additionally requires a host `php` interpreter on
`PATH`. The observed interpreter was PHP 8.5.9 (cli), Homebrew. The other five
kernels need no host toolchain — Rust included: `rust2cpg` never invokes
`cargo`, it only reads the manifest the runner synthesizes.

For each case the runner materializes the case's declared fixture files in an
isolated temporary workspace, then executes one non-interactive Joern process:

```bash
joern --script adapters/joern/queries/kernel.sc \
  --param inputPath=<workspace> \
  --param language=<JAVASRC|JSSRC|PYTHONSRC|RUBYSRC|PHP|RUST> \
  --param sourceName=<source function> \
  --param sinkName=<sink function> \
  --param outputPath=reports/raw/joern-<language>-kernel/<case id>.json
```

The process runs with its working directory inside the per-case scratch root,
so Joern's own console project — and therefore each case's CPG — is created and
destroyed per case and no case can observe another's graph. The scratch root is
removed after the evidence is retained.

Joern has no `case.json` model reference. The v0.3.0 freeze digest-binds every
case and fixture byte, so nothing under `cases/` was touched to add this
adapter; the invocation is pinned in the runner instead, the way the Kotlin
Bifrost run pins its policy.

## Case selection

Each command selects, runner-side:

```text
language == "java" | "javascript" | "python" | "ruby" | "php" | "rust"
track == "taint"
score_tier == "core"
```

For the two 16-template languages that have not been expanded — Ruby and PHP —
that is exactly 32 assertions — one positive and one negative for each of the 16 scored
templates in
`docs/applicability-matrix.md`, all under the `benchmark-controlled` model
profile. Rust's exception-catch cell is **inapplicable**
(`docs/applicability-matrix.md` and `docs/rust-kernel.md` record why), and so is
its challenge-tier reflective-invocation cell
(`docs/challenge-tier.md`), so the Rust kernel selects the other 27
templates — **54 assertions** since its challenge row rolled out — exactly as
the Semgrep and CodeQL Rust selections treat those cells. The `Result`/`?`
`language-extension` pair that stands in for the missing exception-catch cell is
scored on its own tier and is deliberately **not** in this selection: the Joern
Rust kernel is the 54 core assertions and nothing else.

JavaScript moves the other way: its thirteen preregistered challenge templates
have rolled out (`docs/challenge-tier.md`), so its core population is 29
templates — **58 assertions** — and the selector picks all of them up without
any per-adapter change, because the denominator is derived from the rollout
table rather than hard-coded.

Each selection is enforced by the same `validate_kernel_population_with` check
every other kernel uses, against that language's own template set. The six
selections are disjoint, and none of them is a CodeQL or Bifrost population.

## Tagging model

The fixtures declare their own taint endpoints, so the query needs no
per-language source/sink model:

- **sources** — calls to the case's declared source function. The call node
  *is* the value the benchmark says is tainted.
- **sinks** — the positional arguments of calls to the case's declared sink
  function. `argumentIndex > 0` drops the implicit receiver that the JavaScript
  and Python frontends attach as argument 0; the receiver is not part of the
  benchmark's sink contract.

The query is then a single `sinks.reachableByFlows(sources)` under the OSS
data-flow engine, with no per-case, per-template, or per-polarity branching.

The two endpoint identifiers are **read out of the fixture**, never assumed.
The runner resolves each case's `DFB-SOURCE:` and `DFB-SINK:` marker line and
takes the function declared on it. This matters: 56 of the 58 Java assertions
spell the endpoints `dfb_source`/`dfb_sink`, but the two frozen Java
direct-propagation assertions predate that convention and spell them
`directUntrustedInput`/`recordDirect` and
`explicitNegativeUntrustedInput`/`recordExplicitNegative`. An adapter that
assumed the conventional names would have analyzed those two cases with an
empty source and sink set and silently reported them as negatives.

Surface reconciliation is language-specific in exactly two places — how a
marker line declares a function, and what a call to it looks like. JavaScript
reuses the existing ECMAScript dialect unchanged. Java's rules (an identifier
before a parameter list; members reached through `.` alone; `//` comments) are
the same two rules C# and Go already use, but Java is a separately named
dialect so a Java population is never reconciled by a selector spelled for
another language. Python needs its own dialect because its comments open with
`#`, not `//`. PHP needs its own because it accepts *both* `//` and `#` as
line-comment openers, reaches members through `->` and `::`, and uses `.` for
string concatenation rather than member access — so, uniquely, a call preceded
by `.` is a genuine callsite and must not be excluded. Ruby needs its own for a
stronger reason still: its parameter list is optional, so
`def dfb_source # DFB-SOURCE: ...` declares a method with no `(` to read a name
in front of. The Ruby dialect therefore reads the declared name after the `def`
keyword, pairs `#` comments with `.` and `::` member prefixes, and does not
treat a parenless call as a sink callsite — every benchmark sink takes one
positional argument and every fixture spells that call with parentheses.

### The Ruby frontend dispatch

Joern ships `rubysrc2cpg` and its console reports `importCode.ruby` as
available, but the generic `importCode(language = "RUBYSRC")` dispatcher this
script used has no Ruby entry: it raises `No CPG generator exists for language:
RUBYSRC` for every spelling of the identifier. The script therefore dispatches
Ruby through the named `importCode.ruby` frontend — the same generator in the
same console — and leaves every other language on the generic path unchanged.

**Re-checked on 4.0.610, and still needed.** The upgrade was the natural moment
to drop the workaround, so it was probed rather than assumed: a script that
calls `importCode(inputPath = …, language = "RUBYSRC")` against a Ruby fixture
under `4.0.610` still fails with

```text
io.joern.console.ConsoleException: No CPG generator exists for language: RUBYSRC
```

The named-dispatch branch is therefore kept, unchanged, and the comment in
`kernel.sc` now records that it was re-verified against the pinned version
rather than inherited. Rust needs no such branch: the generic dispatcher does
accept `RUST`.

### The Rust crate materialization

`rust2cpg` is the reason the pin moved, and it is the one frontend here that
will not read a loose source file. Handed a bare `.rs` fixture it exits
successfully and produces an **empty** CPG — no methods, no calls — which,
without care, is exactly what a clean negative looks like. It walks a Cargo
crate instead.

So for Rust cases only, the runner writes a minimal `Cargo.toml` into the
per-case temporary workspace beside the fixture it just copied there — the same
`write_rust_cargo_manifest` the CodeQL Rust runner uses, with `[[bin]] path`
pointing straight at the case's own fixture and an empty `[workspace]` table so
Cargo cannot walk out of the scratch directory. Nothing is written beside a
fixture in `cases/`, no case's `fixture_files` changes, and the manifest dies
with the scratch root.

Pointing the binary target at the fixture rather than generating a `src/main.rs`
is what keeps the evidence anchorable. Joern reports each node's location as the
crate-relative path, so with the fixture at the crate root every location comes
back as the case's own anchor filename — `local_chain_positive.rs`, not
`src/main.rs` — and the existing anchor reconciliation matches it with no path
rewriting at all. Had the fixture been moved under `src/`, the reported path
would have had to be mapped back to the anchor file before any flow could be
proved.

`rust2cpg` is **brand new upstream** — this is the first Joern release to ship
it — and its results below are published on that understanding. They are a
snapshot of a young frontend, not a settled characterization of Joern on Rust.

## Outcome semantics

| Outcome | Meaning |
| --- | --- |
| `reached` | Joern produced a flow whose evidence lands on a callsite of the case's own anchored sink function, in the anchored file. |
| `not-reached` | The frontend and engine ran, both benchmark-controlled endpoints were observed in the CPG, and no flow was produced. |
| `inconclusive` | The run completed but its evidence cannot establish the assertion: a source or sink node the query never observed, a flow with no usable or an ambiguous location, or a sink anchor the runner cannot resolve. |
| `unsupported` | The case is outside the documented Joern profile — see the frontend coverage below. No case in the six executed kernels is `unsupported`. |
| `runner-error` | The Joern process failed to spawn, exited non-zero, produced no evidence document, produced unparseable evidence, or the script itself caught a frontend or engine exception. |

`inconclusive`, `unsupported`, and `runner-error` are never normalized to
`not-reached`. The script always writes one JSON document, and it writes
`"state": "runner-error"` with the caught exception rather than an empty flow
list if the frontend or the engine throws — an empty result set that came from
a failure can therefore never look like a negative. Process-level failures
retain the exit status, stdout, and stderr in `<case id>-error.json` beside the
evidence.

A `reached` outcome requires anchor-backed evidence. The retained flow's
element locations are reconciled against the sink function's callsites, the
same reconciliation the CodeQL C#, Go, C, C++, and Rust kernels apply to SARIF.
A `DFB-SINK:` marker sits on the sink *declaration*; the flow legitimately
lands on the *callsite*, so matching does not require the marker's own line.

## Observed results

Joern 4.0.610, build identity `joern-cli:4.0.610`. All six kernels ran on the
same pinned distribution and the same unmodified script, so every retained
Joern report carries one `tool_version` and the single configuration hash
above. Every case in all six kernels executed: 344 retained evidence documents,
zero error documents, zero `inconclusive`, `unsupported`, or `runner-error`
outcomes.

None of the six still stands at the pre-expansion fixture revision
`sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea`, and
none stands at an intermediate wave revision either. The Python, JavaScript,
Java, Rust, PHP, and Ruby kernels were all re-run whole for the v0.4.0 freeze
after every challenge-tier row had rolled out, so all six carry the single
revision
`sha256:13a11ff48f26dba889f76aeb9ef60213a129abe5ebcfcb966da3a2418c12807e`.
`fixture_revision` digests the whole case corpus, so each wave's fixtures
moved it for every run after it; re-running the whole adapter at one revision
is what removes that skew. Reports at different fixture revisions are not
pooled, and each language's expanded assertions are a different population from
the 32 (30 for Rust) it reported in v0.3.0, not a movement within one.

| Kernel | `reached` | `not-reached` | Polarity match |
| --- | --- | --- | --- |
| **Java (`javasrc2cpg`)** | **26** | **32** | **47/58** |
| **JavaScript (`jssrc2cpg`)** | **27** | **31** | **44/58** |
| **Python (`pysrc2cpg`)** | **25** | **33** | **48/58** |
| **PHP (`php2cpg`)** | **25** | **33** | **48/58** |
| **Ruby (`rubysrc2cpg`)** | **23** | **35** | **40/58** |
| **Rust (`rust2cpg`)** | **20** | **34** | **43/54** |

Rust's denominator is 54, not 58, because two cells are inapplicable to it —
`exception-catch` from the classic sixteen and `chal-reflective-invocation`
from the challenge thirteen; the ratios are not comparable across a different
denominator and are not averaged. Split by stratum, Rust is **27/30 on the
classic fifteen — identical case for case to its pre-expansion snapshot, so the
expansion introduced no drift — and 16/24 on its challenge twelve**.

**Java's, Python's, JavaScript's, PHP's, and Ruby's denominators are 58, not
32.** All five challenge-tier rows are rolled out — as is Rust's, at its reduced
54 — so each core is the expanded 29
templates: the sixteen v0.3.0 templates plus the thirteen preregistered
challenge templates ([the challenge tier](../../docs/challenge-tier.md)). Each
report was re-run whole — a whole-population replacement, not an append — and
all six carry the one v0.4.0 fixture revision; no Joern kernel
is left at `sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea`.
Split by stratum, JavaScript is **26/32 on the classic sixteen — identical case
for case to its v0.3.0 snapshot, so the expansion introduced no drift — and
18/26 on the challenge thirteen**, Java is likewise **28/32 on the classic
sixteen, identical case for case to its v0.3.0 snapshot, and 19/26 on the
challenge thirteen**, PHP is **28/32 on the classic sixteen, identical case
for case to its previous snapshot, and 20/26 on the challenge thirteen**,
Python is **28/32 and 20/26**, and Ruby is **26/32 on the classic sixteen, also
identical case for case to its pre-expansion snapshot, and 14/26 on the
challenge thirteen**, all
still with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes. A 58-assertion score and a 32-assertion score are
different populations and are neither compared nor averaged, and each language's
own 28/32 or 26/32 v0.3.0 result and its expanded result are likewise separate
populations of the same name.

Mismatches, verbatim:

**Java** — `reports/joern-java-kernel.json` (58 assertions), 47/58 over the
expanded core: 28/32 on the classic sixteen templates and 19/26 on the
challenge tier.

Classic stratum, 28/32 — the same four as before the expansion, case for case:

- `dfb-taint-java-alias-propagation-positive`: false negative.
- `dfb-taint-java-exception-catch-positive`: false negative.
- `dfb-taint-java-infeasible-branch-negative`: false positive.
- `dfb-taint-java-loop-carried-negative`: false positive.

Challenge strata, 19/26 — A 3/6, B 5/8, C **6/6**, D 5/6:

- `dfb-taint-java-reflective-invocation-positive`: false negative.
- `dfb-taint-java-dispatch-table-positive`: false negative.
- `dfb-taint-java-computed-property-negative`: false positive.
- `dfb-taint-java-callback-registration-positive`: false negative.
- `dfb-taint-java-function-field-positive`: false negative.
- `dfb-taint-java-anonymous-implementation-negative`: false positive.
- `dfb-taint-java-deep-relay-chain-positive`: false negative.

These are approximation character, and the preregistration says so in advance
rather than after the fact. The engine declines to resolve a callee named by a
run-time string or fetched from a map, a field, or a list — so those positives
are missed and their negatives are correct without the callee having been
resolved — while it merges the two anonymous implementations of one interface
and merges two distinct constant keys of one reflected field, producing the two
false positives. The container stratum is answered completely.

`dfb-taint-java-deep-relay-chain-positive` is a **predicted** miss, and the
prediction is on the record before the run: this distribution's
`io.joern.dataflowengineoss.queryengine.EngineConfig` default `maxCallDepth` is
4, verified from the shipped jar, and the challenge chain is deliberately six
hops. **This adapter did not raise that bound.** No `maxCallDepth` override is
configured anywhere in the runner or the script, so the run's identity is the
documented default; had it been raised, that would have been reported as part
of the run's identity rather than tuned in silently.

**JavaScript** — `reports/joern-javascript-kernel.json` (58 assertions)

Classic stratum (16 templates):

- `dfb-taint-javascript-alias-propagation-positive`: false negative.
- `dfb-taint-javascript-exception-catch-positive`: false negative.
- `dfb-taint-javascript-array-element-negative`: false positive.
- `dfb-taint-javascript-infeasible-branch-negative`: false positive.
- `dfb-taint-javascript-loop-carried-negative`: false positive.
- `dfb-taint-javascript-same-object-field-negative`: false positive.

Challenge stratum (13 templates):

- `dfb-taint-javascript-reflective-invocation-positive`: false negative.
- `dfb-taint-javascript-dispatch-table-positive`: false negative.
- `dfb-taint-javascript-function-field-positive`: false negative.
- `dfb-taint-javascript-callback-registration-positive`: false negative.
- `dfb-taint-javascript-map-iteration-positive`: false negative.
- `dfb-taint-javascript-deep-relay-chain-positive`: false negative.
- `dfb-taint-javascript-computed-property-negative`: false positive.
- `dfb-taint-javascript-nested-access-path-negative`: false positive.

The depth-6 relay positive is missed while its negative is correct, at the
distribution's **default** `maxCallDepth` of 4 — nothing was configured up for
this run. That is the outcome
[the challenge tier](../../docs/challenge-tier.md) predicted in writing before
the fixture existed, from this jar's own `EngineConfig` default, and the pair
has to be read together: the negative is a true negative arrived at partly
because the engine cannot see that far. The two-deep context pair is correct
both ways, as is the constant-depth-5 recursive carry.

**Python** — `reports/joern-python-kernel.json` (58 assertions)

Classic stratum, 28/32 — the same four as before the expansion, case for case:

- `dfb-taint-python-alias-propagation-positive`: false negative.
- `dfb-taint-python-exception-catch-positive`: false negative.
- `dfb-taint-python-infeasible-branch-negative`: false positive.
- `dfb-taint-python-loop-carried-negative`: false positive.

Challenge strata, 20/26 — A 3/6, B 6/8, C 6/6, D 5/6:

- `dfb-taint-python-reflective-invocation-positive`: false negative.
- `dfb-taint-python-dispatch-table-positive`: false negative.
- `dfb-taint-python-computed-property-negative`: false positive.
- `dfb-taint-python-function-field-positive`: false negative.
- `dfb-taint-python-callback-registration-positive`: false negative.
- `dfb-taint-python-deep-relay-chain-positive`: false negative.

Stratum A is reported as approximation character rather than skill, per
`docs/challenge-tier.md`: Joern declines the `getattr`-selected and
dict-selected callees (missing both positives, correctly declining both
negatives) while over-approximating the computed-key member access (resolving
the positive and joining two provably distinct constant keys in the negative).
The stratum-D miss is the preregistered prediction: the six-hop relay is
calibrated past the verified `maxCallDepth = 4` default, the adapter did not
raise that bound, and the positive is `not-reached` while the negative is
`not-reached` for the same bounded reason rather than because the engine
refuted it. Per-stratum reading is in
[the Python kernel contract](../../docs/python-kernel.md).

**Ruby** — `reports/joern-ruby-kernel.json` (58 assertions), 40/58 over the
expanded core: 26/32 on the classic sixteen templates and 14/26 on the
challenge tier.

Classic stratum, 26/32 — the same six as before the expansion, case for case:

- `dfb-taint-ruby-alias-propagation-positive`: false negative.
- `dfb-taint-ruby-exception-catch-positive`: false negative.
- `dfb-taint-ruby-argument-position-negative`: false positive.
- `dfb-taint-ruby-call-context-negative`: false positive.
- `dfb-taint-ruby-infeasible-branch-negative`: false positive.
- `dfb-taint-ruby-loop-carried-negative`: false positive.

Challenge strata, 14/26 — A 3/6, B 4/8, C 3/6, D 4/6:

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

Note that `dfb-taint-ruby-deep-relay-chain-positive` is **absent** from this
list: Ruby resolves the depth-6 relay pair correctly, the one measured
departure from the preregistered stratum-D prediction.

**PHP** — `reports/joern-php-kernel.json` (58 assertions), 48/58 over the
expanded core: 28/32 on the classic stratum and 20/26 on the challenge strata
(A 4/6, B 5/8, C 6/6, D 5/6).

Classic — unchanged case for case from its previous snapshot:

- `dfb-taint-php-alias-propagation-positive`: false negative.
- `dfb-taint-php-exception-catch-positive`: false negative.
- `dfb-taint-php-infeasible-branch-negative`: false positive.
- `dfb-taint-php-loop-carried-negative`: false positive.

Challenge:

- `dfb-taint-php-reflective-invocation-positive`: false negative.
- `dfb-taint-php-dispatch-table-positive`: false negative.
- `dfb-taint-php-function-field-positive`: false negative.
- `dfb-taint-php-callback-registration-positive`: false negative.
- `dfb-taint-php-anonymous-implementation-negative`: false positive.
- `dfb-taint-php-deep-relay-chain-positive`: false negative.

**Rust** — `reports/joern-rust-kernel.json` (54 assertions), 43/54 over the
expanded core: 27/30 on the classic fifteen templates and 16/24 on its twelve
challenge templates.

Classic stratum, 27/30 — the same three as before the expansion, case for case:

- `dfb-taint-rust-alias-propagation-positive`: false negative.
- `dfb-taint-rust-infeasible-branch-negative`: false positive.
- `dfb-taint-rust-loop-carried-negative`: false positive.

Challenge stratum, 16/24 — **eight false negatives and zero false positives**:

- `dfb-taint-rust-computed-property-positive`: false negative (stratum A).
- `dfb-taint-rust-dispatch-table-positive`: false negative (stratum A).
- `dfb-taint-rust-closure-capture-positive`: false negative (stratum B).
- `dfb-taint-rust-function-field-positive`: false negative (stratum B).
- `dfb-taint-rust-callback-registration-positive`: false negative (stratum B).
- `dfb-taint-rust-anonymous-implementation-positive`: false negative (stratum B).
- `dfb-taint-rust-map-iteration-positive`: false negative (stratum C).
- `dfb-taint-rust-deep-relay-chain-positive`: false negative (stratum D).

Four mismatching templates recur across the five languages that share the
sixteen v0.3.0 templates — alias propagation through a field and value transfer
to an exception handler are missed everywhere, and the infeasible branch and
the loop-carried kill are over-approximated everywhere — which is what a shared
engine over language-specific frontends should look like. PHP and Java's and
Python's classic strata show exactly that set and nothing else; JavaScript
adds array-element and same-object-field over-approximation; Ruby adds
argument-position and call-context over-approximation.

All six challenge strata are recorded here: Python's, JavaScript's, Java's,
Rust's, PHP's, and Ruby's — one per Joern kernel, the rollout being complete.
JavaScript's divides cleanly: every stratum-A and stratum-B *negative* is
decided correctly while five of those positives are missed — the
under-approximating half of the approximation character the challenge
preregistration described — and the two false positives are the computed-key
and depth-3 sibling reads, which sharpen the field-precision bound the classic
array-element and same-object-field mismatches already show rather than
revealing a new one. Java's divides the same way and answers its container
stratum completely, its two false positives coming from merging the two
anonymous implementations of one interface and two distinct constant keys of
one reflected field. PHP's is the cleanest of the six at 20/26, tied with Python: it also
answers stratum C completely, its single false positive is again the merge of
two anonymous implementations, and — unlike Java — it keeps PHP's *native*
computed property `$holder->{$key}` apart across two distinct constant keys,
which is the same question Java could only ask through `java.lang.reflect.Field`
and failed. Its four false negatives are all positives whose callee is named by
a run-time string, fetched from an array of closures, stored in an object
property, or held in a hook list. All five kernels miss the depth-6 relay
positive for the one preregistered reason: the verified `maxCallDepth = 4`
default, unraised.

Ruby's is the flattest of the six and the only one that breaks the depth
prediction. Strata A and B are almost entirely under-approximating — every
stratum-B result is `not-reached`, so the four negatives are right for the same
reason the four positives are wrong — and stratum C is `not-reached` on all six,
which says `rubysrc2cpg`'s depth-1 field sensitivity does not extend to a
depth-3 accessor chain, to `Hash#each` iteration, or to a field inside an array
element. The one over-approximation is `computed-property`, where the
`instance_variable_set`/`instance_variable_get` pair is carried *and* the two
distinct constant keys are joined. Stratum D is where Ruby departs from the
other five: **the depth-6 relay positive is `reached` and its negative is
`not-reached`**, a correctly discriminated pair past the unraised
`maxCallDepth = 4` default, against the preregistration's stated expectation.
The recursive carry is resolved on the positive and over-approximated on the
`overwrite-kill` negative — the widened recursive summary template 12 exists to
expose — and the k = 2 context pair is `not-reached` on both halves. The
prediction stands in the preregistration unamended; it was made about the
engine's documented default and this is one frontend's measured result against
it. Per-stratum reading is in
[the Ruby kernel contract](../../docs/ruby-kernel.md).

Rust's three classic mismatches are exactly that recurring set intersected with
its own 15 applicable classic templates: it misses the same field-alias
propagation and over-approximates the same infeasible branch and loop-carried
kill, and the fourth recurring mismatch — exception catch — is not a Rust cell
at all. `rust2cpg` decided every one of the 54 assertions, including both
return-relay hops, call-context separation, and object separation, and no case
fell to `inconclusive` on the expanded population either.

Rust's challenge stratum is the sharpest instance so far of the under-approximating
character the preregistration described, and it is the first challenge-stratum
evidence here for a systems language. **Every** stratum-A and stratum-B negative
is decided correctly and **every** stratum-A and stratum-B positive is missed —
6 correct, 6 missed, with not one false positive anywhere in the twelve
challenge templates, where JavaScript and Java each produced two. So on Rust the
frontend declines to resolve an indirect callee rather than merging the
candidates, which is the opposite half of the same design axis and is reported
as character, not as a ranking. Its two container cells that *are* resolved —
the depth-3 nested access path and the per-element object field, both including
their sibling-read negatives — put Rust's field precision deeper than the
classic array-element cell alone establishes, while the `map-iteration` positive
is missed, separating "models a field chain" from "models a container's
iteration protocol". Recursive carry at depth 5 and the two-deep context pair
are both fully correct.

This is published as a snapshot of a frontend that shipped in this release, not
as a settled characterization.

These are published as observed: no fixture was changed, no query was
contorted, and no case was special-cased to move a result.

### Drift from the previous `4.0.432` pin

The five pre-existing kernels were re-run rather than carried over, so the
upgrade's effect on each is measured, not assumed. Four of the five reproduced
`4.0.432` case-for-case:

| Kernel | `4.0.432` | `4.0.610` | Drift |
| --- | --- | --- | --- |
| Java | 28/32 | 28/32 | none; identical mismatch set (classic stratum; the later 58-assertion expansion re-ran it unchanged) |
| JavaScript | 26/32 | 26/32 | none; identical mismatch set (classic stratum; the later 58-assertion expansion re-ran it unchanged) |
| Python | 28/32 | 28/32 | none; identical mismatch set |
| PHP | 28/32 | 28/32 | none; identical mismatch set (classic stratum; the later 58-assertion expansion re-ran it unchanged) |
| Ruby | 26/32 | 26/32 | **same total, different set — four cases moved** (classic stratum; the later 58-assertion expansion re-ran it unchanged) |

That table compares the 16-template population under two Joern pins. The later
expansions of Java, JavaScript, Python, PHP, and Ruby to 58 assertions are
*population* changes, not pin changes, and their 47/58, 44/58, 48/58, 48/58, and
40/58
belong beside neither column.

Ruby's score is unchanged and its outcome distribution is unchanged (18
`reached`, 14 `not-reached`), but the *identity* of its four false positives
changed. Two negatives that `4.0.432` over-approximated are now decided
correctly, and two that it decided correctly are now over-approximated:

- `dfb-taint-ruby-array-element-negative`: false positive under `4.0.432`,
  correct `not-reached` under `4.0.610`. **Improved.**
- `dfb-taint-ruby-same-object-field-negative`: false positive under `4.0.432`,
  correct `not-reached` under `4.0.610`. **Improved.**
- `dfb-taint-ruby-argument-position-negative`: correct `not-reached` under
  `4.0.432`, false positive under `4.0.610`. **Regressed.**
- `dfb-taint-ruby-call-context-negative`: correct `not-reached` under
  `4.0.432`, false positive under `4.0.610`. **Regressed.**

In each case the raw evidence shows the substantive change, not a normalization
artefact: both endpoints are observed in all four CPGs, and the flow count moved
between 1 and 0 in the direction the outcome reports. `rubysrc2cpg` now
separates array elements and same-object fields the way the other frontends do —
the array-element and same-object-field over-approximation JavaScript still
shows is no longer shared with Ruby — while losing argument-position and
call-context separation it previously had. This is drift in the analyzer under
test, and it is a publishable result: nothing in the benchmark changed between
the two runs but the pinned Joern version.

Normalized `witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and retains the full element-by-element path
evidence in the raw document rather than synthesizing normalized witness
markers.

## Frontend coverage

Verified against the pinned distribution — the frontends installed under its
`joern-cli/frontends/` directory and the language identifiers `importCode`
accepts.

Installed frontends: `abap2cpg`, `c2cpg`, `csharpsrc2cpg`, `ghidra2cpg`,
`gosrc2cpg`, `javasrc2cpg`, `jimple2cpg`, `jssrc2cpg`, `kotlin2cpg`, `php2cpg`,
`pysrc2cpg`, `rubysrc2cpg`, `rust2cpg`, `swiftsrc2cpg`.

`rust2cpg` and `abap2cpg` are new since `4.0.432`. There is still no Scala
*source* frontend.

| Benchmark language | Frontend in the pinned distribution | Status |
| --- | --- | --- |
| Java | `javasrc2cpg` | Executed here |
| JavaScript | `jssrc2cpg` | Executed here |
| Python | `pysrc2cpg` | Executed here |
| Ruby | `rubysrc2cpg` | Executed here |
| PHP | `php2cpg` | Executed here (needs a host `php` on `PATH`) |
| C | `c2cpg` | Available, not yet in scope |
| C++ | `c2cpg` | Available, not yet in scope |
| C# | `csharpsrc2cpg` | Available, not yet in scope |
| Go | `gosrc2cpg` | Available, not yet in scope |
| Kotlin | `kotlin2cpg` | Available, not yet in scope (unchanged by Kotlin's challenge-tier expansion: no Joern Kotlin slice exists here to expand) |
| TypeScript | `jssrc2cpg` | Available, not yet in scope |
| Rust | `rust2cpg` | Executed here (new in `4.0.610`; needs a synthesized Cargo manifest) |
| **Scala** | **none (source)** | **Explicitly unsupported** (unchanged by Scala's challenge-tier expansion: the 26 challenge fixtures are single-file `scalac`-clean sources on exactly the same terms as the 32 classic ones, so all 58 assertions fall outside the profile) |

Rust was explicitly unsupported under `4.0.432`, which shipped no Rust frontend
and no Rust identifier in `Languages.ALL`. `4.0.610` ships `rust2cpg` and the
generic `importCode` dispatcher accepts `RUST`, which is what makes the Rust
kernel runnable — and is why the pin moved. Scala has no
*source* frontend; `jimple2cpg` consumes JVM bytecode, which is a different
extraction contract from the single-source-file, no-build fixtures this
benchmark ships, so Scala is likewise out of profile rather than merely
unimplemented. "Available, not yet in scope" means the frontend exists and the
language could be added later — it is not a claim about how well it performs,
because it has not been run.

TypeScript is the row most likely to be misread, so it is stated twice.
`jssrc2cpg` parses `.ts`, but this adapter has **no TypeScript slice**: no
`run-joern-typescript-kernel` command, no TypeScript selection, no
`reports/joern-typescript-kernel.json`. The TypeScript challenge-tier wave
(`docs/typescript-kernel.md`) did not invent one — standing up a language slice
is its own change, not a side effect of landing fixtures — so TypeScript has no
Joern evidence at any denominator, classic or expanded.

The same applies to Go, and for the same reason. The pinned distribution ships
`gosrc2cpg` as a standalone frontend under `joern-cli/frontends/gosrc2cpg`, but
this adapter has **no Go slice**: no `run-joern-go-kernel` command, no Go
selection, no `reports/joern-go-kernel.json`. The Go challenge-tier wave
(`docs/go-kernel.md`) did not invent one either, so Go has no Joern evidence at
any denominator, classic or expanded. Its absence from the run is a scope fact,
not a result about Joern on Go.

C++ is the same story with a different frontend. `c2cpg` ships in the pinned
distribution, but this adapter has **no C++ slice**: no
`run-joern-cpp-kernel` command, no C++ selection, no
`reports/joern-cpp-kernel.json`. The C++ challenge-tier wave
(`docs/cpp-kernel.md`) did not build one either, so C++ — like C — has no
Joern evidence at any denominator.

The same holds for **C**, whose challenge-tier row has since rolled out to 24
templates / 48 assertions. `c2cpg` ships with the pinned distribution and the
row above records C as "Available, not yet in scope", but there is no
`run-joern-c-kernel` command, no C selection, and no
`reports/joern-c-kernel.json`. The C challenge-tier wave
(`docs/c-kernel.md`) did not create one, so C has no Joern evidence at any
denominator either. Absence of a slice is not a Joern result about C.

## Model assumptions

- The `benchmark-controlled` profile applies: the query is given the same
  source and sink identities the Bifrost and CodeQL kernels are given, and
  nothing from Joern's own default source/sink models is used.
- Only the OSS data-flow engine's default semantics are used **by the
  kernels**. No custom semantics, no additional propagation or sanitizer
  models, and no engine configuration are supplied to `kernel.sc`. The
  taint-modeling matrix is the one population that supplies semantics, through
  its own `modeling.sc` and its own per-language semantics file; it never
  touches the kernel script and is never pooled with a kernel population.
- The source is the source call's return value; the sink is the sink call's
  positional arguments. Receiver arguments are excluded.
- One CPG per case, always built cold from source; no CPG is reused between
  cases or between languages.
- Each fixture is analyzed exactly as it is checked in — a single source file
  and no compilation step. The Rust kernel is the one exception to "no
  generated build manifest": `rust2cpg` cannot see a loose `.rs` file, so a
  minimal `Cargo.toml` is synthesized per workspace. It adds no code, no
  dependency, and no compilation; the fixture bytes are still exactly the
  checked-in ones.

Joern results are not a proxy for any other adapter's population, and no
Joern population is evidence for another Joern language.

## Taint-modeling matrix

`run-joern-modeling --language <language>` runs that language's twenty-four
assertions of the
[benchmark-controlled taint-modeling matrix](../../docs/modeling-matrix.md),
writing `reports/joern-<language>-modeling.json` with retained evidence under
`reports/raw/joern-<language>-modeling/`. Java is wave M1's first language; see
[the Java modeling report](../../docs/java-modeling.md).

This is the one place where the "no custom semantics" statement above does not
apply, and it is scoped so that it still applies everywhere else. The kernels
supply no semantics and no engine configuration, and `queries/kernel.sc` is
untouched by this population. The modeling matrix supplies both, through two
files that are hash-bound together into the modeling report and into nothing
else:

| File | Carries |
| --- | --- |
| `queries/modeling.sc` | the roles whose native Joern surface is a query root — `source`, `sink`, and `entry-point` |
| `semantics/model-<language>.semantics` | the roles whose surface is a `FlowSemantic` — `propagator`, `sanitizer`, `summary`, `store-write`, `store-read` |

The script loads the semantics file with `FullNameSemanticsParser` and installs
it as the engine's whole `Semantics` via `FullNameSemantics.fromList`. No
default catalog is layered underneath, so an entity with no entry is one the
benchmark did not declare — which is exactly what the undeclared siblings of
this matrix's negatives need.

Index convention in the semantics files: 0 is the receiver, 1..n the declared
parameters counted from one, and -1 the return value. The
[model declaration language](../../docs/modeling-matrix.md#the-model-declaration-language)
counts parameters from **0**, so its `in: 0` is index 1 here. A method named with
no mapping at all is `NilSemantics` — taint that arrives does not leave — which
is both the `sanitizer` role and the explicit no-flow declaration the `summary`
role's negatives need.

**The semantics files carry no comments.** The pinned 4.0.610
`FullNameSemanticsParser` returns an empty declaration list for a file whose
first line is a `//` comment; that was verified against the pinned distribution
rather than assumed, so the files are declarations only and their commentary
lives in the language's modeling document.

The modeling normalization is not the kernel's. A kernel run that bound zero
source or zero sink nodes is `inconclusive`, because on a kernel an unobserved
endpoint means the run never saw the assertion. On the modeling tier an
unobserved endpoint is frequently the measurement itself — a declared-source
negative's sibling is undeclared *on purpose* — so zero bound nodes is a correct
and informative answer there, retained in the diagnostics rather than converted
into incomplete evidence. A run that produced no CPG at all is still
`runner-error`.

Invocation, one non-interactive process per case, in a per-case scratch root:

```bash
joern --script adapters/joern/queries/modeling.sc \
  --param inputPath=<workspace> \
  --param language=<JAVASRC|JSSRC|PYTHONSRC> \
  --param semanticsPath=adapters/joern/semantics/model-<language>.semantics \
  --param outputPath=reports/raw/joern-<language>-modeling/<case id>.json
```

### Observed: Java

`reports/joern-java-modeling.json`, 4.0.610, 24 results: 12 `reached` and 12
`not-reached`, **20/24 correct** — ten true positives, ten true negatives, two
false positives, two false negatives, no `inconclusive` and no `runner-error`.
Categories S, Z, and E are 4/4; P and O are 3/4 and B is 2/4.

The load-bearing counterfactual is a documented probe: removing only the
`Clean.scrub` line from the nine-entry semantics file turns both category-Z
negatives from no flows to one flow each, while template 7's negative — which
depends on the still-declared `Bridge.hold` — is unchanged.

Three engine facts account for the four misses, and each is published as
observed rather than tuned around:

- **Positional fidelity is not enforced.** `Opaque.select` is declared index
  2 → return and taint at the undeclared index 1 reaches the sink. A separate
  three-way probe separates this from "the model was ignored": replacing the
  mapping with `NilSemantics` removes both cells' findings, and removing the
  entry entirely lets the engine walk the reflective body instead. The mapping
  is applied; its index is not what selects the argument.
- **A `FlowPath` access-path destination does not discriminate.**
  `Bridge.deposit` declared `1 -> 2 "payload"` also taints the sibling field
  `box.spare`. The preregistration named exactly this cell as unverified.
- **The persistence roundtrip does not close.** Both category-B declarations
  load and both negatives are correct, but no flow crosses from `Store.put`'s
  value parameter to `Store.get`'s return in either the type-bound or the
  instance-bound spelling.

All three are recorded as *proposed* amendments on the preregistration, not
applied: a partition cell revised from a result is a result being relabelled.
See [the Java modeling report](../../docs/java-modeling.md).

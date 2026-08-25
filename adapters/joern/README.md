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
analyzers. See [the PHP kernel contract](../../docs/php-kernel.md).

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

For the four 16-template languages that have not been expanded that is exactly
32 assertions — one positive and one negative for each of the 16 scored
templates in
`docs/applicability-matrix.md`, all under the `benchmark-controlled` model
profile. Rust's exception-catch cell is **inapplicable**
(`docs/applicability-matrix.md` and `docs/rust-kernel.md` record why), so the
Rust kernel selects the other 15 templates — 30 assertions — exactly as the
Semgrep and CodeQL Rust selections treat that cell. The `Result`/`?`
`language-extension` pair that stands in for the missing cell is scored on its
own tier and is deliberately **not** in this selection: the Joern Rust kernel is
the 30 core assertions and nothing else.

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
takes the function declared on it. This matters: 30 of the 32 Java assertions
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
above. Every case in all six kernels executed: 242 retained evidence documents,
zero error documents, zero `inconclusive`, `unsupported`, or `runner-error`
outcomes.

Four of the six ran against fixture revision
`sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea`.
The Python and JavaScript kernels were each re-run whole after that language's
challenge-tier row was rolled out, and each carries the expanded corpus
revision current when it ran —
`sha256:3e7a8de5e1eefb18e8166af0ccdf309bccf1d5c26026893a4513f1943926ab1f` for
Python and
`sha256:64ef139f452fd296bb26463bc552e5e5998ca4bb4584d45565d858424814bde9` for
JavaScript. Reports at different fixture revisions are not pooled, and each
language's 58 assertions are a different population from the 32 it reported in
v0.3.0, not a movement within one.

| Kernel | `reached` | `not-reached` | Polarity match |
| --- | --- | --- | --- |
| Java (`javasrc2cpg`) | 16 | 16 | 28/32 |
| **JavaScript (`jssrc2cpg`)** | **27** | **31** | **44/58** |
| **Python (`pysrc2cpg`)** | **25** | **33** | **48/58** |
| Ruby (`rubysrc2cpg`) | 18 | 14 | 26/32 |
| PHP (`php2cpg`) | 16 | 16 | 28/32 |
| Rust (`rust2cpg`) | 16 | 14 | 27/30 |

Rust's denominator is 30, not 32, because its exception-catch cell is
inapplicable; the ratios are not comparable across a different denominator and
are not averaged.

**Python's and JavaScript's denominators are 58, not 32.** Both challenge-tier
rows are rolled out, so each core is the expanded 29 templates: the sixteen
v0.3.0 templates plus the thirteen preregistered challenge templates
([the challenge tier](../../docs/challenge-tier.md)). Each report was re-run
whole — a whole-population replacement, not an append — and each carries the
expanded corpus revision current when it ran, while the other four still carry
`sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea`.
Split by stratum, JavaScript is **26/32 on the classic sixteen — identical case
for case to its v0.3.0 snapshot, so the expansion introduced no drift — and
18/26 on the challenge thirteen**, still with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes. A 58-assertion score and a
32-assertion Java score are different populations and are neither compared nor
averaged, and each language's own 28/32 v0.3.0 or 26/32 v0.3.0 result and its
expanded result are likewise separate populations of the same name.

Mismatches, verbatim:

**Java** — `reports/joern-java-kernel.json`

- `dfb-taint-java-alias-propagation-positive`: false negative.
- `dfb-taint-java-exception-catch-positive`: false negative.
- `dfb-taint-java-infeasible-branch-negative`: false positive.
- `dfb-taint-java-loop-carried-negative`: false positive.

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

**Ruby** — `reports/joern-ruby-kernel.json`

- `dfb-taint-ruby-alias-propagation-positive`: false negative.
- `dfb-taint-ruby-exception-catch-positive`: false negative.
- `dfb-taint-ruby-argument-position-negative`: false positive.
- `dfb-taint-ruby-call-context-negative`: false positive.
- `dfb-taint-ruby-infeasible-branch-negative`: false positive.
- `dfb-taint-ruby-loop-carried-negative`: false positive.

**PHP** — `reports/joern-php-kernel.json`

- `dfb-taint-php-alias-propagation-positive`: false negative.
- `dfb-taint-php-exception-catch-positive`: false negative.
- `dfb-taint-php-infeasible-branch-negative`: false positive.
- `dfb-taint-php-loop-carried-negative`: false positive.

**Rust** — `reports/joern-rust-kernel.json`

- `dfb-taint-rust-alias-propagation-positive`: false negative.
- `dfb-taint-rust-infeasible-branch-negative`: false positive.
- `dfb-taint-rust-loop-carried-negative`: false positive.

Four mismatching templates recur across the five languages that share the
sixteen v0.3.0 templates — alias propagation through a field and value transfer
to an exception handler are missed everywhere, and the infeasible branch and
the loop-carried kill are over-approximated everywhere — which is what a shared
engine over language-specific frontends should look like. Java, PHP, and
Python's classic stratum show exactly that set and nothing else; JavaScript
adds array-element and same-object-field over-approximation; Ruby adds
argument-position and call-context over-approximation.

Two challenge strata are recorded here, Python's and JavaScript's. JavaScript's
divides cleanly: every stratum-A and stratum-B *negative* is decided correctly
while five of those positives are missed — the under-approximating half of the
approximation character the challenge preregistration described — and the two
false positives are the computed-key and depth-3 sibling reads, which sharpen
the field-precision bound the classic array-element and same-object-field
mismatches already show rather than revealing a new one.

Rust's three mismatches are exactly that recurring set intersected with its own
15 applicable templates: it misses the same field-alias propagation and
over-approximates the same infeasible branch and loop-carried kill, and the
fourth recurring mismatch — exception catch — is not a Rust cell at all.
`rust2cpg` decided every one of the 30 assertions, including both return-relay
hops, call-context separation, and object separation. That is a stronger first
showing than a brand-new frontend has to give, and it is published as a
snapshot of a frontend that shipped in this release, not as a settled
characterization.

These are published as observed: no fixture was changed, no query was
contorted, and no case was special-cased to move a result.

### Drift from the previous `4.0.432` pin

The five pre-existing kernels were re-run rather than carried over, so the
upgrade's effect on each is measured, not assumed. Four of the five reproduced
`4.0.432` case-for-case:

| Kernel | `4.0.432` | `4.0.610` | Drift |
| --- | --- | --- | --- |
| Java | 28/32 | 28/32 | none; identical mismatch set |
| JavaScript | 26/32 | 26/32 | none; identical mismatch set (classic stratum; the later 58-assertion expansion re-ran it unchanged) |
| Python | 28/32 | 28/32 | none; identical mismatch set |
| PHP | 28/32 | 28/32 | none; identical mismatch set |
| Ruby | 26/32 | 26/32 | **same total, different set — four cases moved** |

That table compares the 16-template population under two Joern pins. Python's
later expansion to 58 assertions is a *population* change, not a pin change,
and its 48/58 belongs beside neither column.

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
| Kotlin | `kotlin2cpg` | Available, not yet in scope |
| TypeScript | `jssrc2cpg` | Available, not yet in scope |
| Rust | `rust2cpg` | Executed here (new in `4.0.610`; needs a synthesized Cargo manifest) |
| **Scala** | **none (source)** | **Explicitly unsupported** |

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

## Model assumptions

- The `benchmark-controlled` profile applies: the query is given the same
  source and sink identities the Bifrost and CodeQL kernels are given, and
  nothing from Joern's own default source/sink models is used.
- Only the OSS data-flow engine's default semantics are used. No custom
  semantics, no additional propagation or sanitizer models, and no engine
  configuration are supplied.
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

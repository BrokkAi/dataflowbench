# Joern adapter

The Joern adapter runs the Java, JavaScript, Python, and PHP propagation kernels
through Joern's source frontends and its OSS data-flow engine. Each language is
its own population: its own case selection, its own frontend, its own
normalized report, and its own retained-evidence directory. Joern shares one
CPG query language and one data-flow engine across all four, exactly as CodeQL
shares a standard library across its packs; the populations are kept apart by
the selector and the report paths, never by the engine.

PHP is the one language here for which Joern is not a third opinion: the pinned
CodeQL CLI has no PHP support at all, so Bifrost and Joern are PHP's only two
analyzers. See [the PHP kernel contract](../../docs/php-kernel.md).

## Pinned distribution

| Item | Value |
| --- | --- |
| Version | `4.0.432` (`joern --version`) |
| Build identity | `joern-cli:4.0.432` |
| Installation | `/usr/local/bin/joern` → `/opt/joern/joern-cli/joern` |
| Query script | `adapters/joern/queries/kernel.sc` |
| Configuration hash | `2ce582b8a5d1efd4e6025153893178bfb900cce933826826d63371d632a64564` |

The pinned distribution reports no build SHA separate from its released
version, so the released version *is* the build identity. That is recorded
literally rather than padded with a synthetic identifier.

## Invocation

```bash
cargo run -- run-joern-java-kernel       --joern /usr/local/bin/joern
cargo run -- run-joern-javascript-kernel --joern /usr/local/bin/joern
cargo run -- run-joern-python-kernel     --joern /usr/local/bin/joern
cargo run -- run-joern-php-kernel        --joern /usr/local/bin/joern
```

`php2cpg` shells out to its bundled PHP-Parser
(`frontends/php2cpg/bin/php-parser/php-parser-4.15.10.phar`), which is itself a
PHP program, so the PHP kernel additionally requires a host `php` interpreter on
`PATH`. The observed interpreter was PHP 8.5.9 (cli), Homebrew. The other three
kernels need no host toolchain.

For each case the runner materializes the case's declared fixture files in an
isolated temporary workspace, then executes one non-interactive Joern process:

```bash
joern --script adapters/joern/queries/kernel.sc \
  --param inputPath=<workspace> \
  --param language=<JAVASRC|JSSRC|PYTHONSRC|PHP> \
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
language == "java" | "javascript" | "python" | "php"
track == "taint"
score_tier == "core"
```

That is exactly 32 assertions per language — one positive and one negative for
each of the 16 scored templates in `docs/applicability-matrix.md`, all under the
`benchmark-controlled` model profile — enforced by the same
`validate_kernel_population_with` check every other kernel uses. The four
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
`#`, not `//`. PHP needs its own for the opposite reason: it accepts *both* `//`
and `#` as line-comment openers, reaches members through `->` and `::`, and uses
`.` for string concatenation rather than member access — so, uniquely, a call
preceded by `.` is a genuine callsite and must not be excluded.

## Outcome semantics

| Outcome | Meaning |
| --- | --- |
| `reached` | Joern produced a flow whose evidence lands on a callsite of the case's own anchored sink function, in the anchored file. |
| `not-reached` | The frontend and engine ran, both benchmark-controlled endpoints were observed in the CPG, and no flow was produced. |
| `inconclusive` | The run completed but its evidence cannot establish the assertion: a source or sink node the query never observed, a flow with no usable or an ambiguous location, or a sink anchor the runner cannot resolve. |
| `unsupported` | The case is outside the documented Joern profile — see the frontend coverage below. No case in the four executed kernels is `unsupported`. |
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

Joern 4.0.432. The Java, JavaScript, and Python kernels ran at fixture revision
`sha256:1b1b8d5cd90dc4bbdb0675a5a6b6b58315d2328b157e9074f8db13e17736b816`; the
PHP kernel was added later and ran at
`sha256:9630d095eb41e3d6c1aef8423e8d4381c6c601ceefb9146b5b42bc14f94ad612`, the
revision that includes its own 30 new fixtures. Every case in all four kernels
executed: 128 retained evidence documents, zero error documents, zero
`inconclusive`, `unsupported`, or `runner-error` outcomes.

| Kernel | `reached` | `not-reached` | Polarity match |
| --- | --- | --- | --- |
| Java (`javasrc2cpg`) | 16 | 16 | 28/32 |
| JavaScript (`jssrc2cpg`) | 18 | 14 | 26/32 |
| Python (`pysrc2cpg`) | 16 | 16 | 28/32 |
| PHP (`php2cpg`) | 16 | 16 | 28/32 |

Mismatches, verbatim:

**Java** — `reports/joern-java-kernel.json`

- `dfb-taint-java-alias-propagation-positive`: false negative.
- `dfb-taint-java-exception-catch-positive`: false negative.
- `dfb-taint-java-infeasible-branch-negative`: false positive.
- `dfb-taint-java-loop-carried-negative`: false positive.

**JavaScript** — `reports/joern-javascript-kernel.json`

- `dfb-taint-javascript-alias-propagation-positive`: false negative.
- `dfb-taint-javascript-exception-catch-positive`: false negative.
- `dfb-taint-javascript-array-element-negative`: false positive.
- `dfb-taint-javascript-infeasible-branch-negative`: false positive.
- `dfb-taint-javascript-loop-carried-negative`: false positive.
- `dfb-taint-javascript-same-object-field-negative`: false positive.

**Python** — `reports/joern-python-kernel.json`

- `dfb-taint-python-alias-propagation-positive`: false negative.
- `dfb-taint-python-exception-catch-positive`: false negative.
- `dfb-taint-python-infeasible-branch-negative`: false positive.
- `dfb-taint-python-loop-carried-negative`: false positive.

**PHP** — `reports/joern-php-kernel.json`

- `dfb-taint-php-alias-propagation-positive`: false negative.
- `dfb-taint-php-exception-catch-positive`: false negative.
- `dfb-taint-php-infeasible-branch-negative`: false positive.
- `dfb-taint-php-loop-carried-negative`: false positive.

The four mismatching templates are consistent across all four languages —
alias propagation through a field and value transfer to an exception handler
are missed everywhere, and the infeasible branch and the loop-carried kill are
over-approximated everywhere — which is what a shared engine over four
language-specific frontends should look like. Java, Python, and PHP show
exactly that set and nothing else; JavaScript additionally over-approximates
array-element and same-object-field separation. These are published as
observed: no fixture was changed, no query was contorted, and no case was
special-cased to move a result.

Normalized `witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and retains the full element-by-element path
evidence in the raw document rather than synthesizing normalized witness
markers.

## Frontend coverage

Verified against the pinned distribution — `joern --help`, the frontends
installed under `/opt/joern/joern-cli/frontends/`, and the language identifiers
`importCode` accepts.

Installed frontends: `c2cpg`, `csharpsrc2cpg`, `ghidra2cpg`, `gosrc2cpg`,
`javasrc2cpg`, `jimple2cpg`, `jssrc2cpg`, `kotlin2cpg`, `php2cpg`, `pysrc2cpg`,
`rubysrc2cpg`, `swiftsrc2cpg`.

| Benchmark language | Frontend in the pinned distribution | Status |
| --- | --- | --- |
| Java | `javasrc2cpg` | Executed here |
| JavaScript | `jssrc2cpg` | Executed here |
| Python | `pysrc2cpg` | Executed here |
| PHP | `php2cpg` | Executed here (needs a host `php` on `PATH`) |
| C | `c2cpg` | Available, not yet in scope |
| C++ | `c2cpg` | Available, not yet in scope |
| C# | `csharpsrc2cpg` | Available, not yet in scope |
| Go | `gosrc2cpg` | Available, not yet in scope |
| Kotlin | `kotlin2cpg` | Available, not yet in scope |
| Ruby | `rubysrc2cpg` | Available, not yet in scope |
| TypeScript | `jssrc2cpg` | Available, not yet in scope |
| **Rust** | **none** | **Explicitly unsupported** |
| **Scala** | **none (source)** | **Explicitly unsupported** |

Rust has no frontend in this distribution and no language identifier in
`Languages.ALL`, so a Joern Rust kernel cannot be run at all here. Scala has no
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
- Each fixture is analyzed exactly as it is checked in — a single source file,
  no generated build manifest, no compilation step.

Joern results are not a proxy for any other adapter's population, and no
Joern population is evidence for another Joern language.

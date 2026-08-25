# Semgrep CE adapter

The Semgrep adapter runs the Java, JavaScript, TypeScript, Python, Go, Ruby,
PHP, Kotlin, Rust, C, and C++ propagation kernels through the **Community
Edition (open-source) taint engine only**, and scores only the partition of each
kernel that the pinned distribution documents that engine as covering. Every
language is its own population: its own case selection, its own committed rule
file, its own normalized report, and its own retained-evidence directory.

This is a deliberately *bounded* adapter. Semgrep CE is not a whole-program
data-flow engine and the benchmark does not pretend it is. Nine of the sixteen
scored templates are outside its documented profile; those assertions are
`unsupported` by a declared-capability decision taken from the case metadata
**before** Semgrep is invoked, and they are never counted as false negatives.

Four of the eleven front ends are not GA in the pinned distribution — Kotlin is
recorded `beta`, and Rust, C, and C++ are recorded `alpha`. That label is
retained on every assertion and stated in the coverage table below. It is a
property of the *parser*, and it never moves a case between the scored and
`unsupported` partitions; see [Front-end maturity](#front-end-maturity).

## Pinned distribution

| Item | Value |
| --- | --- |
| Version | `1.174.0` (`semgrep --version`) |
| Edition | Community Edition / open-source engine, pinned with `--oss-only` |
| Build identity | `semgrep-oss:1.174.0` |
| Installation | Homebrew (`brew install semgrep`), `/opt/homebrew/bin/semgrep` → `../Cellar/semgrep/1.174.0/bin/semgrep` |
| Rules | `adapters/semgrep/rules/<language>.yaml` (eleven committed files) |
| Language table | `semgrep_interfaces/lang.json`, shipped inside the pinned wheel |
| Configuration hash | `865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100` |

The pinned distribution reports no build SHA separate from its released
version, so the released version *is* the build identity, recorded literally
rather than padded with a synthetic identifier. The Pro Engine is not installed
and is never installed by this adapter; `--oss-only` ("Run using only the OSS
engine, even if the Semgrep Pro toggle is on") is passed on every scan, and the
normalizer additionally refuses any finding whose `engine_kind` is not `OSS`.

## The documented taint scope

The scored profile is not a guess and it is not inferred from misses. It is
read off the pinned distribution's own documentation.

`semgrep scan --help`, verbatim:

- `--pro-intrafile` — "Intra-file inter-procedural taint analysis. Implies
  `--pro-languages`. Requires Semgrep Pro Engine."
- `--pro` — "Inter-file analysis and Pro languages (currently Apex, C#, and
  Elixir). Requires Semgrep Pro Engine."
- `--pro-path-sensitive` — "Path sensitivity. Implies `--pro-intrafile`.
  Requires Semgrep Pro Engine."

So in the CE engine there is **no interprocedural taint at all**, no cross-file
taint, and no path sensitivity: each of those three is sold as a Pro feature.
The bundled `CHANGELOG.md` bounds the heap the same way. CE gained only
"Experimental support for basic field-sensitive taint tracking" (0.113.0) and
"Java: Support for basic field sensitivity via getters and setters", while
"Pro: taint-mode: Added basic support for 'index sensitivity'" and "Pro:
Taint-mode now supports inter-procedural field-sensitivity for JS/TS" are both
recorded as Pro. The CE engine is documented as a control-flow-sensitive
intraprocedural data-flow analysis and nothing more.

The scored profile is therefore: **intra-file, intraprocedural,
flow-sensitive, path-insensitive taint.**

That profile is a property of the *engine*, and the engine is shared. It is not
restated per language and it is not adjusted for a language whose front end is
less mature; see the next section.

## Front-end maturity

The pinned distribution carries its own machine-readable language table,
`semgrep_interfaces/lang.json`, and every entry has a `maturity` field. The
values are read off that file rather than off the marketing docs, and they are
retained verbatim:

| Kernel | `id` | `maturity` | Corroborating `CHANGELOG.md` entry |
| --- | --- | --- | --- |
| Java, JavaScript, TypeScript, Python, Go, Ruby, PHP | `java`, `js`, `ts`, `python`, `go`, `ruby`, `php` | `ga` | — |
| Kotlin | `kotlin` | **`beta`** | "New language Kotlin with experimental support."; later, "The Kotlin tree-sitter parser has been updated to the latest available grammar significantly improving Kotlin support in Semgrep. (kotlin-parser)" |
| Rust | `rust` | **`alpha`** | "Rust: Beta support for Rust. (gh-6545)" — the changelog's historical announcement is *ahead* of the shipped table, which still records `alpha`; the shipped table is what this adapter cites |
| C | `c` | **`alpha`** | "Using C++ tree-sitter as a failsafe pattern parser for C (gh-8905)" |
| C++ | `cpp` | **`alpha`** | "Pre-alpha support for C++ as a new target language"; later, "experimental support for C++" |

This is handled the way the CodeQL adapter handles its Rust extractor's public
preview status: the label is recorded, prominently, wherever the numbers are —
in this README, in every `<case id>-unsupported.json` capability-decision
document (`language_maturity`), and, because
`schemas/result.schema.json` has no report-level field for it, on the first
`diagnostics` entry of **every** normalized Semgrep result:

```text
pinned Semgrep CE records the Rust front end's maturity as "alpha"
(semgrep_interfaces/lang.json `maturity`); the label describes the parser,
not the scored partition
```

What the label explicitly does **not** do is change any decision.
`semgrep_capability_exclusion` reads `feature_tags` and
`expected_analysis_capability` out of the case and nothing else — it cannot see
a language, let alone a maturity — so an `alpha` front end is scored on exactly
the partition a `ga` one is. A regression tests that two cases identical but for
`language` receive the identical exclusion decision. If a less mature parser
performs worse, that shows up as a published mismatch, not as a quietly widened
`unsupported` partition.

Taint mode was verified to function on each of the four before any of them was
wired up: a one-rule `mode: taint` scan of that language's own
`direct-positive` fixture, under the pinned `--oss-only` invocation, returned
exit 0, an empty `errors` array, no skipped path, and one `OSS` finding on the
sink callsite. None of the four had to be recorded unsupported.

## Case selection and the bounded partition

Each command selects, runner-side:

```text
language == the kernel's own language
track == "taint"
score_tier == "core"
```

For four of the eleven that is exactly 32 assertions — one positive and one
negative for each of the 16 scored templates in
`docs/applicability-matrix.md` — all under the `benchmark-controlled` model
profile, enforced by the same `validate_kernel_population_with` check every
other kernel uses.

**Rust is 30, not 32, and C is 48.** `docs/applicability-matrix.md` classifies
the exception-catch cell as *inapplicable* to both, for different reasons, so
their classic core denominator is the fifteen-template
`KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH` set the CodeQL and Bifrost C and
Rust kernels already use. C's challenge row has since rolled out — nine
applicable challenge templates on top of those fifteen, so 24 templates and 48
assertions — while Rust's has not. An inapplicable cell reduces only its own
language's denominator, never any other's.

The construct each of those two languages uses instead lives on the
`language-extension` tier — C's `dfb-taint-c-error-code-return-positive` and
`dfb-taint-c-goto-cleanup-positive`, Rust's
`dfb-taint-rust-result-error-propagation-{positive,negative}` — and the
`score_tier == "core"` filter is what keeps all four out of the core run, where
they would silently inflate the denominator. A test asserts by name that none of
them appears in any Semgrep population.

The eleven selections are disjoint, and none of them is a CodeQL, Joern, or
Bifrost population.

The bounded profile then narrows what is **scored**, never what is selected.
The partition is by the case's own `feature_tags` and
`expected_analysis_capability.kind`, and the rule is identical in every
language:

| Templates | `feature_tags` | Outcome | Why |
| --- | --- | --- | --- |
| `direct-propagation`, `arithmetic-expression-propagation`, `local-multi-step-chain`, `local-overwrite-kill`, `loop-carried-kill`, `branch-join`, `infeasible-branch` | `intraprocedural` | **scored** (7 templates, 14 assertions) | Inside the documented CE profile. |
| `return-relay-one-hop`, `argument-position-separation`, `call-context-separation` | `interprocedural-one-hop` | `unsupported` (3 templates, 6 assertions) | CE has no interprocedural taint (`--pro-intrafile` is Pro). |
| `return-relay-two-hop` | `interprocedural-deep` | `unsupported` (1 template, 2 assertions) | Same, over two hops. |
| `alias-propagation-separation`, `object-separation`, `array-element-separation`, `same-object-field-separation`, `exception-catch` | `heap-access-path` (Go's `exception-catch` is tagged `exceptional`) | `unsupported` (5 templates, 10 assertions; **4 templates, 8 assertions** in C and Rust, which have no exception-catch cell) | CE documents only *experimental basic* field sensitivity; index sensitivity and inter-procedural field sensitivity are Pro. |

**14 scored in every one of the eleven kernels**, because all seven
intraprocedural templates are applicable in all eleven languages. Only the
`unsupported` remainder differs with the denominator: 18 in the five
16-template kernels, **16 in C and Rust**, and **44 in Python, JavaScript,
TypeScript, and Go**, whose challenge-tier rows are rolled out.

| Kernel | Selected | Scored | `unsupported` |
| --- | --- | --- | --- |
| Java, Ruby, PHP, Kotlin, C++ | 32 | 14 | 18 |
| C, Rust | 30 | 14 | 16 |
| **Python, JavaScript, TypeScript, Go** | **58** | **14** | **44** |

The last two rows are the challenge tier. Their core denominators are the
expanded template sets — the sixteen v0.3.0 templates plus that language's
preregistered challenge templates, thirteen for the 58-assertion kernels and
twelve for C++, whose `reflective-invocation` cell the preregistration
classifies inapplicable — and **every challenge assertion falls in the
`unsupported` partition**, exactly as the preregistered partition below fixed
in advance. Nothing about the scored partition was rewritten for the tier, and
the scored subset stays at 14 assertions: the expansion moved the
`unsupported` remainder from 18 to 42 or 44 and moved nothing else.

The decision is taken by `semgrep_capability_exclusion` from the case JSON
alone; an excluded case never reaches a Semgrep process, so it cannot produce an
empty finding list that later reads as a miss. Each excluded case retains an
`<case id>-unsupported.json` document naming the declared capability, the
feature tags, the documented boundary it falls outside, and the front end's
recorded maturity.

Note what is deliberately **not** excluded. `branch-join`, `infeasible-branch`,
and `loop-carried-kill` carry a `path-sensitivity` semantic dimension, and
path sensitivity is a Pro feature. They stay scored anyway: the CE engine can
*express* those flows, it just over-approximates them, and an over-approximation
is a publishable false positive rather than a capability gap. Excluding them
would have hidden exactly the two mismatches this adapter reports.

## Preregistered partition for the challenge tier

This section was written **before any challenge fixture existed and before
Semgrep had been pointed at one**, and it has not been edited since. It is a
preregistration in the sense
[the challenge-tier document](../../docs/challenge-tier.md) uses the word: the
partition is fixed here, from the pinned distribution's documentation, while the
outcomes are still unknown, and a later wave must not adjust it after seeing
results. A defect in it is corrected by a documented amendment, never by a
silent edit. Python's wave, the first to land challenge fixtures, changed
nothing in this table, and no wave since has — including C's, which exercises
only nine of the thirteen rows because the other four templates are
inapplicable to the language and therefore never selected at all.

The decision is implemented as `CHALLENGE_SEMGREP_PARTITION` in `src/main.rs`,
keyed by `template_id` and consulted *before* the `feature_tags` rule. Keying it
by template rather than by tags is deliberate: it means no fixture author's tag
choices — and no observed result — can move a challenge case between the scored
and `unsupported` partitions once the fixtures land.

**All thirteen are `unsupported` by declared capability.** That is not a
convenience and it is not a scoreboard failure. The classic partition above
scores exactly one shape — a purely local value flow inside a single function —
because that is the only shape the pinned CE engine documents itself as
analyzing. A challenge template is a challenge template precisely *because* its
flow routes through dispatch, a function value, a container or a computed key, a
deep field chain, or a call chain, and the CE documentation places every one of
those outside the engine. None of the thirteen is a pure local value flow. The
same documented boundary that already excludes `array-element-separation` and
`same-object-field-separation` — single-function cases both — excludes the
single-function challenge templates too.

| Stratum | Template | CE decision | Documented reason |
| --- | --- | --- | --- |
| A | `chal-reflective-invocation` | `unsupported` | The callee is resolved from a run-time string and the sink is inside that callee's body. CE has no interprocedural taint at all (`--pro-intrafile` is Pro), and nothing in the pinned CE documentation claims to resolve a reflective handle. |
| A | `chal-computed-property` | `unsupported` | Single-function, but the write and the read locate a member by a run-time key. CE documents only "Experimental support for basic field-sensitive taint tracking", while "Pro: taint-mode: Added basic support for 'index sensitivity'" places keyed access in Pro. Same boundary as the already-excluded `array-element-separation`. |
| A | `chal-dispatch-table` | `unsupported` | The callee is a function value fetched from a stdlib map; both the call-graph edge and the sink are interprocedural. |
| B | `chal-closure-capture` | `unsupported` | The sink is inside a closure body invoked from a different function than the one that captured the value. |
| B | `chal-function-field` | `unsupported` | Needs field sensitivity beyond CE's experimental basic support *and* the interprocedural step CE documents as Pro. |
| B | `chal-callback-registration` | `unsupported` | Registration and driver are different methods; inversion of control is interprocedural by construction. |
| B | `chal-anonymous-implementation` | `unsupported` | Resolving the call-graph edge to an unnamed implementation and following taint into it are both outside the CE engine. |
| C | `chal-map-iteration` | `unsupported` | Retrieval by iterating a container's entries is not within CE's documented "basic field-sensitive" support, and index sensitivity is recorded as Pro. |
| C | `chal-nested-access-path` | `unsupported` | A field chain of depth ≥ 3; CE documents only *basic* experimental field sensitivity. |
| C | `chal-element-object` | `unsupported` | Element separation and field separation in one query; index sensitivity is Pro and CE's field sensitivity is experimental and basic. |
| D | `chal-deep-relay-chain` | `unsupported` | A six-hop interprocedural relay. `docs/challenge-tier.md` already records stratum D as beyond CE's documented scope. |
| D | `chal-recursive-carry` | `unsupported` | A recursive summary is interprocedural; CE has no interprocedural taint. |
| D | `chal-context-pair-depth2` | `unsupported` | Two-level context sensitivity; CE has no interprocedural taint and therefore no calling context to be sensitive to. |

The consequence, stated in advance: when a language's challenge fixtures land,
its Semgrep kernel's selected population grows with its rollout row while its
**scored** subset stays at 14 assertions, and the `unsupported` remainder grows
by twice that language's applicable challenge count. That is the honest
description of a bounded engine measured against a harder population, and it is
not a gap to paper over. Every excluded case still retains its
`<case id>-unsupported.json` capability-decision document, and an `unsupported`
outcome is never converted into a false negative.

## The taint model

The `benchmark-controlled` profile applies. The rules state the same endpoint
contract every other kernel pins — taint from the case's declared source
endpoint to its declared sink endpoint — and none of Semgrep's own registry
rules, source models, or sink models are used. Issue #15 will later formalize a
cross-tool taint-modeling matrix; these rules are the endpoint-contract
instantiation of it, and are expected to be restated in its terms once it lands.

Each `adapters/semgrep/rules/<language>.yaml` is a single `mode: taint` rule
with one `pattern-sources` entry and one `pattern-sinks` entry, carrying two
placeholder tokens:

```yaml
pattern-sources:
  - pattern: __DFB_SOURCE__(...)
pattern-sinks:
  - pattern: __DFB_SINK__(...)
```

Because the endpoint identifiers vary per fixture, the runner resolves
`__DFB_SOURCE__` and `__DFB_SINK__` per case from that fixture's own
`DFB-SOURCE:` and `DFB-SINK:` marker lines — the same
`benchmark_endpoint_names` the Joern kernels use, so the two adapters cannot
drift. This matters: 56 of the 58 Java assertions spell the endpoints
`dfb_source`/`dfb_sink`, but the two frozen Java direct-propagation assertions
predate that convention and spell them `directUntrustedInput`/`recordDirect`
and `explicitNegativeUntrustedInput`/`recordExplicitNegative`. A rule that
assumed the conventional names would have analyzed those two cases with an
empty source and sink set and silently reported them as negatives.

Nothing else is templated. There is no per-case, per-template, or per-polarity
branching. Keeping the retained configuration honest is a two-part contract:

- the **committed** templates are hash-bound — every report's
  `configuration_hash` is a SHA-256 over *all eleven* rule files, so a change to
  any one of them invalidates every retained Semgrep report. Adding the four new
  rule files did exactly that, so all eleven kernels were re-run against the new
  hash rather than four being appended beside seven reports citing a hash that
  no longer describes the committed rule set;
- the **resolved** rule each case was actually analyzed under is retained
  verbatim beside its finding document as `<case id>-rule.yaml`.

Ruby is the one kernel whose rule differs in substance. A Ruby call's parameter
list is optional and every Ruby fixture spells the source call parenless
(`first = dfb_source`), so the parenthesised pattern alone would match nothing;
its `pattern-sources` is a `pattern-either` over both spellings. The sink keeps
the single parenthesised form in every language, because every benchmark sink
takes one positional argument and every fixture spells that call with
parentheses. The other ten rule files are byte-identical apart from the
`languages:` key and the comment header — which for Kotlin, Rust, C, and C++
also records that front end's maturity — but each is still its own committed
file so a population is never scored by a rule spelled for another language.

All eleven kernels resolve their endpoints to `dfb_source`/`dfb_sink` except the
two frozen Java assertions named above; a test resolves every scored case of the
four newly covered kernels through its chosen dialect and fails if any one of
them cannot name its own endpoints.

## Invocation

```bash
cargo run -- run-semgrep-java-kernel       --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-javascript-kernel --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-typescript-kernel --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-python-kernel     --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-go-kernel         --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-ruby-kernel       --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-php-kernel        --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-kotlin-kernel     --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-rust-kernel       --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-c-kernel          --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-cpp-kernel        --semgrep /opt/homebrew/bin/semgrep
```

No host toolchain is required for any of the eleven: each case is a single
checked-in source file with no build step, and Semgrep parses it directly. This
is the adapter's one structural advantage over CodeQL here — the C, C++, Rust,
and Kotlin CodeQL kernels each need a build or a generated manifest, and Semgrep
needs neither a `Cargo.toml`, a compiler, nor a JVM. For
each scored case the runner materializes the case's declared fixture files in
an isolated temporary workspace and executes one Semgrep process:

```bash
semgrep scan --metrics=off --oss-only --disable-version-check \
  --no-git-ignore --quiet --json \
  --config reports/raw/semgrep-<language>-kernel/<case id>-rule.yaml \
  <workspace>
```

`--metrics=off` is passed on every invocation; nothing is reported to
semgrep.dev, no rule is fetched from the registry, and `--config` always names
a local committed-and-resolved file. The scratch workspace is removed after the
evidence is retained.

Semgrep has no `case.json` model reference. The v0.3.0 freeze digest-binds every
case and fixture byte, so nothing under `cases/` was touched to add this
adapter; the invocation is pinned in the runner instead, the way the Joern
kernels and the Kotlin Bifrost run pin theirs.

## Outcome semantics

| Outcome | Meaning |
| --- | --- |
| `reached` | Semgrep produced a CE finding on a callsite of the case's own anchored sink function, in the anchored file. |
| `not-reached` | The scan opened the fixture, Semgrep reported no error and skipped no rule, and it produced no finding. |
| `unsupported` | The case is outside the documented CE profile, decided from its declared capability metadata before Semgrep was invoked. |
| `inconclusive` | The run completed but its evidence cannot establish the assertion: a scan that opened no target, a finding with no usable or an ambiguous location, or a sink anchor the runner cannot resolve. |
| `runner-error` | The process failed to spawn, exited non-zero, emitted unparseable JSON, reported anything in its own `errors` array, skipped the benchmark rule, or produced a finding from an engine other than the pinned CE engine. |

`inconclusive`, `unsupported`, and `runner-error` are never normalized to
`not-reached`. Semgrep exits 0 with or without findings and reserves higher
codes for its own failures, so any non-zero status is a runner error and can
never be read as an empty finding list. A non-empty `errors` array is likewise
a runner error even though the accompanying `results` array is a well-formed
empty list — and `raw_special_outcome`, the freeze's raw-evidence guard, now
refuses that combination too, so no such document can ever be frozen next to a
clean negative.

A `reached` outcome requires anchor-backed evidence. A Semgrep finding is a
single location rather than a path, so reconciliation is the one-location form
of the Joern flow match: the finding's own file and line must land on a
callsite of the case's anchored sink. A `DFB-SINK:` marker sits on the sink
*declaration*; the finding legitimately lands on the *callsite*, so matching
does not require the marker's own line.

## Observed results

Semgrep CE 1.174.0. Seven kernels ran against fixture revision
`sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea`; the
Python, JavaScript, Java, TypeScript, Kotlin, Go, C++, and C kernels were
each re-run whole after that
language's challenge-tier row was rolled out and carry the expanded corpus
revision current when each ran —
`sha256:3e7a8de5e1eefb18e8166af0ccdf309bccf1d5c26026893a4513f1943926ab1f` for
Python,
`sha256:61c06a78b95b86764d3c220cfefd7af37373db64b15ae0b76c6ebf924217ab2e` for
JavaScript,
`sha256:cf571f29e434030019d5e8f8361319b0bb3b4d6c4c752bd65860e07bfcf26bbc` for
Java,
`sha256:2c906faeb98b48d1aba7da7bc80a78c4084051b84efac6ac3a1b74f54c843fd2` for
TypeScript. `sha256:7ac23321e5d0974ed9087b9642ee3c88b3f3af014ba507330131da30fbb9b4d7` for
Kotlin, and reports at different
fixture revisions are not pooled. The configuration hash is unchanged across
all eleven: no rule file was touched.

All eleven kernels ran. 546 assertions: 154 executed against Semgrep, 392
excluded by declared capability. Zero `inconclusive` and zero `runner-error`
outcomes; 154 retained finding documents, 154 retained resolved rule files, 324
retained capability-decision documents, and zero error documents. Every figure
here is counted from the committed reports and evidence directories on this
tree, never extrapolated from a previous wave's total.

| Kernel | `maturity` | Selected | `reached` | `not-reached` | `unsupported` | Polarity match (scored subset) |
| --- | --- | --- | --- | --- | --- | --- |
| **Java** | `ga` | **58** | 9 | 5 | **44** | 12/14 |
| **JavaScript** | `ga` | **58** | 9 | 5 | **44** | 12/14 |
| **TypeScript** | `ga` | **58** | 9 | 5 | **44** | 12/14 |
| **Python** | `ga` | **58** | 9 | 5 | **44** | 12/14 |
| **Go** | `ga` | **58** | 9 | 5 | **44** | 12/14 |
| Ruby | `ga` | 32 | 9 | 5 | 18 | 12/14 |
| PHP | `ga` | 32 | 9 | 5 | 18 | 12/14 |
| **Kotlin** | **`beta`** | **58** | 9 | 5 | **44** | 12/14 |
| **Rust** | **`alpha`** | **30** | 9 | 5 | **16** | 12/14 |
| **C** | **`alpha`** | **30** | 9 | 5 | **16** | 12/14 |
| **C++** | **`alpha`** | **56** | 9 | 5 | **42** | 12/14 |

The scored subset is 7 positives and 7 negatives per language, the five
expanded denominators included: their 26 challenge assertions are all
`unsupported`, so the scored subset is the same 14 assertions it was, and the
`Selected` column is the only one an expansion moved. Every one of the 7
intraprocedural positives is `reached` in every language — no false negative
anywhere — and 5 of the 7 negatives are `not-reached`.

Java, JavaScript, Python, TypeScript, Kotlin, Go, C++, and C are the eight
expanded populations, and
each changes only the `unsupported` column: all 26 of that language's challenge
assertions are declined by declared capability, and its scored 14 are the same
14 assertions with the same 12/14 result as before the expansion. A larger
`unsupported` count on a larger population is coverage arithmetic, not a worse
engine.

The four non-GA front ends score exactly what the seven GA ones score. That is
worth stating plainly rather than quietly: the maturity label predicted nothing
about the result on this population, because the population's scored partition
exercises only local propagation and killing inside one function, which is the
part of a front end that matures first. It is *not* evidence that these parsers
are as good as the GA ones in general — nothing here tests a macro, a template,
a coroutine, or a trait, and 14 assertions is a narrow instrument.

Mismatches, verbatim, and identical in all eleven languages:

- `dfb-taint-<language>-infeasible-branch-negative`: false positive.
- `dfb-taint-<language>-loop-carried-negative`: false positive.

### An expanded core changes the excluded partition and nothing else

Java's, JavaScript's, Python's, and TypeScript's cores each now carry the
thirteen [challenge-tier](../../docs/challenge-tier.md) templates, so each
selection grew from 32 to 58 assertions; C++'s carries the twelve the
preregistration classifies applicable to it, growing from 32 to 56. Each one's
**scored subset is still 14, and still 12/14**, with the same two false
positives: no challenge template is tagged `intraprocedural`, so none of them
enters the scored partition. All 26 challenge assertions — 24 for C++ — are
`unsupported` in each language, decided by the preregistered
`CHALLENGE_SEMGREP_PARTITION` before Semgrep was invoked, so not one reached a
Semgrep process and none can read as a false negative. Each retained reason is
the per-template rationale the preregistration fixed — the documented CE
boundary that template falls outside, quoted from the pinned distribution's own
documentation — rather than a generic restatement of the tag rule, and it is
keyed by template ID, so no fixture's `feature_tags` and no observed result can
move a case between the partitions after the fact. A bounded engine declining a
harder tier wholesale is the preregistered expectation and correct behavior, not
a gap to paper over.

Both are exactly what the documentation predicts. `--pro-path-sensitive`
("Path sensitivity. Requires Semgrep Pro Engine") says the CE engine does not
refute the infeasible branch, and the loop-carried kill needs the same
reasoning about which paths can actually execute. A flow-sensitive,
path-insensitive engine over-approximates both and reports the flow. That the
two mismatches are the *same two* across eleven independent language front ends
— including three `alpha` ones and a `beta` one — is what a shared engine
should look like: the mismatch is the engine's, not the parser's.

These are published as observed: no fixture was changed, no rule was contorted,
and no case was moved between the scored and `unsupported` partitions to
improve a number.

Normalized `witness_checkpoints` are empty for every case: the adapter records
anchor-backed finding outcomes and retains Semgrep's full native `--json`
document rather than synthesizing normalized witness markers.

## Language coverage

Verified against the pinned distribution — `semgrep show supported-languages`,
the shipped `semgrep_interfaces/lang.json` maturity table, and the
`--pro-languages` help text.

| Benchmark language | Pinned CE `id` | `maturity` | Status |
| --- | --- | --- | --- |
| Java | `java` | `ga` | Executed here |
| JavaScript | `js` | `ga` | Executed here |
| TypeScript | `ts` | `ga` | Executed here |
| Python | `python` | `ga` | Executed here |
| Go | `go` | `ga` | Executed here |
| Ruby | `ruby` | `ga` | Executed here |
| PHP | `php` | `ga` | Executed here |
| Kotlin | `kotlin` | **`beta`** | Executed here |
| Rust | `rust` | **`alpha`** | Executed here |
| C | `c` | **`alpha`** | Executed here |
| C++ | `cpp` | **`alpha`** | Executed here |
| Scala | `scala` | `ga` | **Recorded only — maintainer decision, not a tool limitation** |
| **C#** | **Pro-only** | `ga` | **Explicitly unsupported** |

**Scala is a maintainer decision.** The pinned distribution records `scala` at
`ga` maturity, which is *more* mature than three of the four languages added
here, and nothing in the CE engine, the taint mode, or the benchmark's Scala
kernel blocks it. It is left recorded-only because the maintainer scoped it out,
and it is written down here as such so nobody later reads its absence as
evidence that Semgrep CE cannot analyze Scala. It can; the run has simply not
been commissioned. Scala remains single-analyzer coverage in
[`docs/scala-kernel.md`](../../docs/scala-kernel.md) until it is. Scala's
challenge-tier expansion to **29 templates / 58 assertions** does not change
this: no Semgrep Scala slice was built for it, and the preregistered
`CHALLENGE_SEMGREP_PARTITION` therefore never sees a Scala case in either
partition. The decision is restated for the expanded population rather than
quietly inherited.

**C# is a tool limitation.** It is named in the pinned CLI's own
`--pro-languages` text — "Pro languages (currently Apex, C#, and Elixir).
Requires Semgrep Pro Engine" — so a Semgrep **CE** C# kernel cannot be run here
at all, however the language appears in `semgrep show supported-languages` and
whatever maturity the shipped table records for it. The Pro Engine is not
installed and is never installed by this adapter, so this exclusion is
permanent under the current pin, not a scoping choice.

No new `AnchorDialect` was needed for any of the four. C, C++, and Rust already
had arms, added for the CodeQL kernels. Kotlin was checked against the real
fixtures rather than assumed: its markers sit on `fun name(params)`
declarations, `parameter_list_function_name` reads the identifier immediately
before the parameter list off exactly that shape, every Kotlin fixture calls its
sink receiverlessly, `.` is the only member operator that could precede the
name (`::` is a reference, never a call, as in Java), and `//` opens a comment.
That is the Java arm's contract in full, so Kotlin reuses it; a Kotlin arm would
have been a copy of it under a different name. The check is a test, not a
claim — it resolves all 14 scored Kotlin cases through the Java arm.

## Model assumptions

- The `benchmark-controlled` profile applies: the rule is given the same source
  and sink identities the Bifrost, CodeQL, and Joern kernels are given, and
  nothing from Semgrep's own registry or default models is used.
- Only the CE (OSS) engine's default taint semantics are used. No propagators,
  no sanitizers, no taint labels, no `options:` block, and no Pro feature.
- The source is the source call itself; the sink is the sink call. No receiver
  or argument-position refinement is applied beyond the call pattern.
- One process per case, always cold; no scan observes another case's files.
- Each fixture is analyzed exactly as it is checked in — a single source file,
  no generated build manifest, no compilation step.
- A front end's recorded maturity is retained evidence about the parser and is
  never an input to the scored/`unsupported` partition.

Semgrep results are not a proxy for any other adapter's population, no Semgrep
population is evidence for another Semgrep language, and the scored 14-assertion
subset is never comparable to another tool's full 32- or 30-assertion kernel.

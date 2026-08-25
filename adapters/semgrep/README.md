# Semgrep CE adapter

The Semgrep adapter runs the Java, JavaScript, TypeScript, Python, Go, Ruby, and
PHP propagation kernels through the **Community Edition (open-source) taint
engine only**, and scores only the partition of each kernel that the pinned
distribution documents that engine as covering. Every language is its own
population: its own case selection, its own committed rule file, its own
normalized report, and its own retained-evidence directory.

This is a deliberately *bounded* adapter. Semgrep CE is not a whole-program
data-flow engine and the benchmark does not pretend it is. Nine of the sixteen
scored templates are outside its documented profile; those assertions are
`unsupported` by a declared-capability decision taken from the case metadata
**before** Semgrep is invoked, and they are never counted as false negatives.

## Pinned distribution

| Item | Value |
| --- | --- |
| Version | `1.174.0` (`semgrep --version`) |
| Edition | Community Edition / open-source engine, pinned with `--oss-only` |
| Build identity | `semgrep-oss:1.174.0` |
| Installation | Homebrew (`brew install semgrep`), `/opt/homebrew/bin/semgrep` → `../Cellar/semgrep/1.174.0/bin/semgrep` |
| Rules | `adapters/semgrep/rules/<language>.yaml` (seven committed files) |
| Configuration hash | `9f63e0d815c646341c868a2e9ea2c0215ebe53dedaa9d01faaf52d8a2201983e` |

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

## Case selection and the bounded partition

Each command selects, runner-side:

```text
language == "java" | "javascript" | "typescript" | "python" | "go" | "ruby" | "php"
track == "taint"
score_tier == "core"
```

That is exactly 32 assertions per language — one positive and one negative for
each of the 16 scored templates in `docs/applicability-matrix.md`, all under the
`benchmark-controlled` model profile — enforced by the same
`validate_kernel_population_with` check every other kernel uses. The seven
selections are disjoint, and none of them is a CodeQL, Joern, or Bifrost
population.

The bounded profile then narrows what is **scored**, never what is selected.
The partition is by the case's own `feature_tags` and
`expected_analysis_capability.kind`, and it is identical in every language:

| Templates | `feature_tags` | Outcome | Why |
| --- | --- | --- | --- |
| `direct-propagation`, `arithmetic-expression-propagation`, `local-multi-step-chain`, `local-overwrite-kill`, `loop-carried-kill`, `branch-join`, `infeasible-branch` | `intraprocedural` | **scored** (7 templates, 14 assertions) | Inside the documented CE profile. |
| `return-relay-one-hop`, `argument-position-separation`, `call-context-separation` | `interprocedural-one-hop` | `unsupported` (3 templates, 6 assertions) | CE has no interprocedural taint (`--pro-intrafile` is Pro). |
| `return-relay-two-hop` | `interprocedural-deep` | `unsupported` (1 template, 2 assertions) | Same, over two hops. |
| `alias-propagation-separation`, `object-separation`, `array-element-separation`, `same-object-field-separation`, `exception-catch` | `heap-access-path` (Go's `exception-catch` is tagged `exceptional`) | `unsupported` (5 templates, 10 assertions) | CE documents only *experimental basic* field sensitivity; index sensitivity and inter-procedural field sensitivity are Pro. |

14 scored and 18 `unsupported` in every one of the seven kernels. The decision
is taken by `semgrep_capability_exclusion` from the case JSON alone; an excluded
case never reaches a Semgrep process, so it cannot produce an empty finding list
that later reads as a miss. Each excluded case retains an
`<case id>-unsupported.json` document naming the declared capability, the
feature tags, and the documented boundary it falls outside.

Note what is deliberately **not** excluded. `branch-join`, `infeasible-branch`,
and `loop-carried-kill` carry a `path-sensitivity` semantic dimension, and
path sensitivity is a Pro feature. They stay scored anyway: the CE engine can
*express* those flows, it just over-approximates them, and an over-approximation
is a publishable false positive rather than a capability gap. Excluding them
would have hidden exactly the two mismatches this adapter reports.

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
drift. This matters: 30 of the 32 Java assertions spell the endpoints
`dfb_source`/`dfb_sink`, but the two frozen Java direct-propagation assertions
predate that convention and spell them `directUntrustedInput`/`recordDirect`
and `explicitNegativeUntrustedInput`/`recordExplicitNegative`. A rule that
assumed the conventional names would have analyzed those two cases with an
empty source and sink set and silently reported them as negatives.

Nothing else is templated. There is no per-case, per-template, or per-polarity
branching. Keeping the retained configuration honest is a two-part contract:

- the **committed** templates are hash-bound — every report's
  `configuration_hash` is a SHA-256 over *all seven* rule files, so a change to
  any one of them invalidates every retained Semgrep report;
- the **resolved** rule each case was actually analyzed under is retained
  verbatim beside its finding document as `<case id>-rule.yaml`.

Ruby is the one kernel whose rule differs in substance. A Ruby call's parameter
list is optional and every Ruby fixture spells the source call parenless
(`first = dfb_source`), so the parenthesised pattern alone would match nothing;
its `pattern-sources` is a `pattern-either` over both spellings. The sink keeps
the single parenthesised form in every language, because every benchmark sink
takes one positional argument and every fixture spells that call with
parentheses. The other six rule files are byte-identical apart from the
`languages:` key and the comment header, but each is still its own committed
file so a population is never scored by a rule spelled for another language.

## Invocation

```bash
cargo run -- run-semgrep-java-kernel       --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-javascript-kernel --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-typescript-kernel --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-python-kernel     --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-go-kernel         --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-ruby-kernel       --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-semgrep-php-kernel        --semgrep /opt/homebrew/bin/semgrep
```

No host toolchain is required for any of the seven: each case is a single
checked-in source file with no build step, and Semgrep parses it directly. For
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

Semgrep CE 1.174.0, fixture revision
`sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea`.
All seven kernels ran. 224 assertions: 98 executed against Semgrep, 126
excluded by declared capability. Zero `inconclusive` and zero `runner-error`
outcomes; 98 retained finding documents, 98 retained resolved rule files, 126
retained capability-decision documents, and zero error documents.

| Kernel | `reached` | `not-reached` | `unsupported` | Polarity match (scored subset) |
| --- | --- | --- | --- | --- |
| Java | 9 | 5 | 18 | 12/14 |
| JavaScript | 9 | 5 | 18 | 12/14 |
| TypeScript | 9 | 5 | 18 | 12/14 |
| Python | 9 | 5 | 18 | 12/14 |
| Go | 9 | 5 | 18 | 12/14 |
| Ruby | 9 | 5 | 18 | 12/14 |
| PHP | 9 | 5 | 18 | 12/14 |

The scored subset is 7 positives and 7 negatives per language. Every one of the
7 intraprocedural positives is `reached` in every language — no false negative
anywhere — and 5 of the 7 negatives are `not-reached`.

Mismatches, verbatim, and identical in all seven languages:

- `dfb-taint-<language>-infeasible-branch-negative`: false positive.
- `dfb-taint-<language>-loop-carried-negative`: false positive.

Both are exactly what the documentation predicts. `--pro-path-sensitive`
("Path sensitivity. Requires Semgrep Pro Engine") says the CE engine does not
refute the infeasible branch, and the loop-carried kill needs the same
reasoning about which paths can actually execute. A flow-sensitive,
path-insensitive engine over-approximates both and reports the flow. That the
two mismatches are the *same two* across seven independent language front ends
is what a shared engine should look like.

These are published as observed: no fixture was changed, no rule was contorted,
and no case was moved between the scored and `unsupported` partitions to
improve a number.

Normalized `witness_checkpoints` are empty for every case: the adapter records
anchor-backed finding outcomes and retains Semgrep's full native `--json`
document rather than synthesizing normalized witness markers.

## Language coverage

Verified against the pinned distribution — `semgrep show supported-languages`
and the `--pro-languages` help text.

| Benchmark language | Pinned CE support | Status |
| --- | --- | --- |
| Java | `java` | Executed here |
| JavaScript | `js` | Executed here |
| TypeScript | `ts` | Executed here |
| Python | `python` | Executed here |
| Go | `go` | Executed here |
| Ruby | `ruby` | Executed here |
| PHP | `php` | Executed here |
| Kotlin | `kotlin` | Available, not yet in scope |
| Rust | `rust` | Available, not yet in scope |
| Scala | `scala` | Available, not yet in scope |
| C | `c` | Available, not yet in scope |
| C++ | `cpp` | Available, not yet in scope |
| **C#** | **Pro-only** | **Explicitly unsupported** |

C# is named in the pinned CLI's own `--pro-languages` text — "Pro languages
(currently Apex, C#, and Elixir). Requires Semgrep Pro Engine" — so a Semgrep
**CE** C# kernel cannot be run here at all, however the language appears in
`semgrep show supported-languages`. "Available, not yet in scope" means the CE
parser exists and the language could be added later; it is not a claim about
how well it performs, because it has not been run. Kotlin and Scala would each
additionally need a new `AnchorDialect`, which the seven executed languages did
not.

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

Semgrep results are not a proxy for any other adapter's population, no Semgrep
population is evidence for another Semgrep language, and the scored 14-assertion
subset is never comparable to another tool's full 32-assertion kernel.

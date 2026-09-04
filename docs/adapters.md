# Adapter contract

An adapter executes a real supported tool surface, captures its raw output,
and normalizes only the states in `schemas/result.schema.json`: `reached`,
`not-reached`, `inconclusive`, `unsupported`, and `runner-error`. The
step-ordered integration walkthrough for a new adapter is
[adding-an-adapter.md](adding-an-adapter.md); this document stays normative
over it.

Canonical cases never contain native rule syntax. Each adapter owns its rules,
models, command line, version discovery, configuration hash, capability notes,
and raw-evidence retention under `adapters/<tool>/` or the adapter's dedicated
report directory.

The initial adapter plan is:

| Tool | Initial profile | Status |
| --- | --- | --- |
| Bifrost | Breadth baseline and per-language propagation kernels | Implemented smoke adapter; kernel runs are reported separately. The Java, JavaScript, PHP, and Scala kernel commands have now been run over their expanded 29-template cores |
| CodeQL | 16-template Java and JavaScript propagation kernels and the 29-template expanded Python kernel | Java, JavaScript, and Python runners implemented as separate language-scoped populations |
| Joern | The Ruby 16-template propagation kernel, the 27-template expanded Rust kernel, and the 29-template expanded Java, Python, JavaScript, and PHP kernels | Implemented as six separate language-scoped populations over one CPG query script |
| Semgrep CE | Supported local analysis only | Implemented as eleven separate language-scoped populations over one committed taint rule per language; only the documented intraprocedural partition is scored. Four front ends are non-GA in the pinned distribution (Kotlin `beta`; Rust, C, C++ `alpha`) and the label is retained without ever changing the partition |
| OpenTaint | Java and Kotlin profile | Implemented as two language-scoped populations over the pinned `analyzer/2026.08.27.17eb0fe` release, both run over their full expanded 58-assertion cores. The whole core is scored — the pinned documentation fences no capability. The first runs' dominant result, a value-kind boundary dropping taint on numeric values, was identified upstream as the default rule configuration and resolved by Amendment A11 (`primitive-tracking: true` in both templates); the amended-template re-runs measure propagation semantics in both languages |
| Infer | C, C++, and Java profile | Implemented as three language-scoped populations over the pinned v1.3.0 release's Pulse taint configuration — the release's one operable taint surface, Quandary being removed — each run over its full expanded core (48, 56, and 58 assertions). The whole core is scored in all three; C and C++ gain their first benchmark-controlled interprocedural second engine |
| FlowDroid | Java and Kotlin profile | Implemented as two language-scoped populations over the pinned 2.15.1 release's command-line analyzer, both run over their full expanded 58-assertion cores. The released CLI analyzes APKs only — verified in the field — so each case materializes a minimal APK from pinned, JVM-only pieces (a D8 dex translation, a committed benchmark-generated binary manifest, a harness entry activity); the whole core is scored, the pinned defaults fencing no capability. Amendments A18 and A19 add its Java modeling row (seven of twelve templates scored, via StubDroid summaries) and its Java tool-native row (a live activation contract over the jar's shipped catalog, all six cells declined on the catalog's own text) |
| Pysa | Python profile | Implemented as one language-scoped population over the pinned pyre-check 0.10.0 release's taint analysis, run over Python's full expanded 58-assertion core. The pin is a pair — the client drives the separately released Pyrefly 1.2.0 front end for call-graph resolution, and without a per-case `pyrefly.toml` that front end exports every call unresolved while exiting cleanly, a verified silent-failure mode the runner guards. The whole core is scored, and Python becomes the five-analyzer kernel issue #82 intended |

No adapter may synthesize a tool result. If a supported case cannot complete,
emit `inconclusive` or `runner-error` with the raw evidence. If it is outside
a documented tool profile, emit `unsupported`; it is excluded from
false-negative interpretation. An incomplete or failed run must never become
`not-reached` merely because the SARIF result list is empty.

## Retained phase timings and the environment stamp

Every run also retains the wall-clock cost of what it invoked, as the
instrumentation half of the latency-characterization tier. The runner times
exactly the analyzer subprocesses the adapter already owns — never analyzer
internals, and never harness compile time, fixture materialization, report
normalization, or validation — using the monotonic clock. Each timed case gets
a sidecar beside its raw evidence, `reports/raw/<slice>/<case-id>-timing.json`,
whose phase labels state the boundary the adapter genuinely observes:
`database-create` and `database-analyze` for CodeQL (extraction including the
traced compile, then query evaluation and SARIF interpretation, which the
pinned CLI performs in one subprocess), `capture` and `analyze` for Infer
(the traced compile, then Pulse evaluation and SARIF emission — the same
two-phase shape as CodeQL's), and `total` for Joern, Semgrep, Bifrost,
OpenTaint, FlowDroid, and Pysa, whose single invocation is indivisible from
the adapter's vantage — Pysa's client drives its front end and its analysis
binary inside one invocation the adapter cannot observe as separate
subprocesses, and FlowDroid's per-case APK materialization happens *before*
the timed subprocess is spawned and is outside its number.
Unequal granularity is stated, not papered over; every adapter's row is
declared in the
[latency tier's granularity table](latency-tier.md#per-adapter-granularity),
the four adapters added in v0.6.0 by
[Amendment A12](latency-tier.md#a12--2026-09-01-the-four-adapters-added-in-v060-take-their-granularity-rows);
any phase timings a tool emits itself ride in its own retained document,
verbatim. Each run also stamps
`reports/raw/<slice>/run-environment.json` once — hardware model, OS, CPU
count — beside the tool identity the run witnessed, because a latency number
is only comparable within the environment that produced it.

Timing fields are **additive metadata**. Their absence in pre-existing frozen
artifacts is not an error, `validate-reports` accepts raw evidence with and
without them, and no correctness outcome may ever read a timing value. A case
arm that never invokes the analyzer — an `unsupported` declaration, a
preregistered partition decision — retains no timing and clears any stale
sidecar from a previous run.

## Reference-tool pin currency

The benchmark's fairness claim depends on the reference tools being current,
not only on Bifrost being current. Pins are therefore re-evaluated on a
schedule rather than drifting until someone notices.

- **At every release freeze-prep**, each adapter's pin is re-evaluated against
  the then-latest stable upstream release. For each analyzer the outcome is
  either a bump to latest stable followed by a re-run, or a **dated reason for
  holding** — a regression in the candidate, a query-pack incompatibility, or
  the reproducibility of an in-flight comparison.
- **Held pins are visible.** The release notes state each pin and its distance
  from upstream latest at freeze time, so staleness is published rather than
  silent.
- **A bump is a full re-run.** A pin bump for any analyzer follows the rule
  Bifrost re-pins already follow: every slice of that adapter re-runs at the
  frozen fixture revision. No freeze ever contains mixed-version evidence for
  one adapter.
- **Vendored rule snapshots are part of the same review.** The Semgrep
  tool-native snapshot (`semgrep/semgrep-rules`) is re-evaluated with the
  engine pin — a native profile read against a stale rules snapshot would
  misstate what the tool ships.
- **Out-of-cycle bumps stay allowed**, as Bifrost fix cycles already are, but
  always land through the same re-pin-PR → re-run → freeze sequence.

Non-goals: no auto-bumping — upstream releases can regress, so every bump is a
measured decision with re-run evidence to show for it; and no chasing Joern's
near-daily releases between freezes, because currency is evaluated at freeze
boundaries.

The policy is operated through the freeze-prep checklist in
[freeze.md](freeze.md#freeze-prep-checklist), whose pin-currency step is the
only place a bump-or-hold decision is taken, and it is published through the
release-notes pin table whose shape is fixed in
[freeze.md](freeze.md#release-notes-template). Each review is recorded below
under a dated heading; a survey taken before the decision is recorded the
same way, marked as moving no declaration.

A pin literal in this repository is either a **pin declaration** — what the
benchmark pins going forward, including standing capability statements about
the pinned distribution — or a **description of retained evidence**: what a
report, a SARIF file, or a dated probe already witnessed. A pin review moves
the declarations only. Retained-evidence descriptions move with the report
bytes at the re-run that produces them, and a dated probe record keeps naming
the version it was probed against until it is re-probed.

### Pin-currency reviews

#### 2026-08-31 — v0.6.0 freeze-prep

The first review under this policy. Every analyzer pin was re-evaluated; each
version below was witnessed from the installed artifact, never taken from a
changelog.

| Analyzer | Pin at v0.5.0 | Outcome | Basis |
| --- | --- | --- | --- |
| CodeQL CLI | 2.26.3 | **Bumped to 2.26.4** | `codeql version --format=json` witnessed 2.26.4, build `6b1e4dee94adb20f90a671f3fc9e04be32eecf65` |
| Semgrep CE | 1.174.0 | **Bumped to 1.175.0** | `semgrep --version` witnessed 1.175.0 (Homebrew) |
| Joern | 4.0.610 | **Bumped to 4.0.614** | `io.joern.joern-cli-4.0.614.jar` in the extracted distribution |
| Bifrost | v0.10.7 | **Held** | v0.10.8 is not yet released upstream as of 2026-08-31; v0.10.7 is latest stable |
| OpenTaint | `analyzer/2026.08.27.17eb0fe` | **Evaluated — current** | Adapter landed 2026-08-31 pinning the release by asset digest; current by construction |
| Infer | v1.3.0 | **Evaluated — current** | Adapter landed 2026-08-31; current by construction |
| FlowDroid | 2.15.1 | **Evaluated — current** | Adapter landed 2026-08-31 pinning the jar by digest; current by construction |
| Pysa | pyre-check 0.10.0 + Pyrefly 1.2.0 | **Evaluated — current** | Adapter landed 2026-08-31 pinning both wheels by digest; current by construction |

**CodeQL query packs are unchanged.** `codeql pack install` was re-run under
2.26.4 for the root Java pack and all nine `adapters/codeql/<lang>` packs. Every
dependency resolved to the version already committed, so no
`codeql-pack.lock.yml` moved and the pack versions this documentation states
are unchanged: `java-all@9.2.3`, `python-all@7.2.3`, `javascript-all@2.9.0`,
`csharp-all@7.1.2`, `go-all@7.2.3`, `cpp-all@12.0.2`, `ruby-all@6.0.3`,
`rust-all@0.2.19`. The `qlpack.yml` manifests pin exact library-pack versions
rather than ranges, so a CLI bump alone cannot move them.

**The vendored Semgrep rules snapshot is held** at
`semgrep/semgrep-rules@40b8c63f75dc7c22c8a77482d73bfb864b146f7e`. The engine
bump to CE 1.175.0 does not disturb the snapshot, whose currency is re-surveyed
with the tool-native profile it feeds.

**Dated probe records were not re-labelled.** Several artifacts — the Joern
`.semantics` headers, `adapters/joern/queries/kernel.sc`, the Semgrep modeling
rule, and the Amendment A2 rationales — record surface facts *verified against*
4.0.610 or CE 1.174.0. Those are retained evidence under the rule above, not
pin declarations, and re-labelling them to the new pins would assert a
verification that was never performed. They are re-probed with the v0.6.0
re-run. The same applies to the CodeQL build-mode findings for Kotlin and Go,
which the re-run re-exercises.

#### 2026-09-01/02 — v0.6.1 Bifrost fix-cycle re-pin

The second review under this policy, and a narrow one: it exists because a
Bifrost fix cycle closed against findings this benchmark published, and the
release's delta is deliberately scoped to that.

| Analyzer | Pin at v0.6.0 | Outcome | Basis |
| --- | --- | --- | --- |
| Bifrost | v0.10.7 | **Bumped to v0.10.8** | `--version` witnessed `bifrost 0.10.8`; `--build-identity` witnessed `419395c8066b9eddfba06aa69c8a151ef4968249` |
| CodeQL CLI | 2.26.4 | **Evaluated — current** | 2.26.4 is still latest stable; no upstream release since the v0.6.0 review |
| Semgrep CE | 1.175.0 | **Evaluated — current** | 1.175.0 is still latest stable |
| Joern | 4.0.614 | **Held** | Upstream daily 4.0.615 is one day newer. Held with this dated reason so the release's delta stays scoped to the Bifrost fix cycle; re-evaluated at the next freeze boundary |
| OpenTaint | `analyzer/2026.08.27.17eb0fe` | **Evaluated — current** | Pinned by asset digest 2026-08-31; unchanged upstream |
| Infer | v1.3.0 | **Evaluated — current** | Pinned 2026-08-31; unchanged upstream |
| FlowDroid | 2.15.1 | **Evaluated — current** | Jar pinned by digest 2026-08-31; unchanged upstream |
| Pysa | pyre-check 0.10.0 + Pyrefly 1.2.0 | **Evaluated — current** | Both wheels pinned by digest 2026-09-01; unchanged upstream |

**What the bump is for.** v0.10.8 closes the fix cycle opened by
BrokkAi/bifrost-dev #2731: all four of that issue's false positives are fixed,
and eight assertions that were previously `inconclusive` are newly decided.

**The bump is taken with a regression published, not held for it.** One
regression was found and filed as BrokkAi/bifrost-dev #2831: the Go
array-element pair, decided under v0.10.7, is now `inconclusive` under
*"value-flow snapshot unsupported (`index_memory`)"*. Holding the pin to keep
one pair decided would suppress a net improvement — four false positives fixed
and eight cells newly decided — and would hide the regression rather than
publish it. The benchmark's obligation runs the other way: the regression is
filed upstream, named here, and lands visibly in the re-run's retained
evidence.

**The vendored Semgrep rules snapshot is held** at
`semgrep/semgrep-rules@40b8c63f75dc7c22c8a77482d73bfb864b146f7e`, per the
policy above: its currency is re-surveyed with the tool-native profile it
feeds, not at every freeze boundary.

**The latency corpus is not re-measured.** It is frozen at v0.6.0, and v0.6.1
does not re-run it. `docs/latency-tier.md` and its artifacts therefore keep
naming **v0.10.7** as the measured environment's Bifrost — those are
descriptions of retained evidence under the rule above, and re-labelling them
to v0.10.8 would assert a measurement that was never performed.

**This review moved declarations only; the evidence re-run followed.** The
twenty Bifrost slices were re-executed on v0.10.8 in a settle-gated quiet
window and are bound by the **v0.6.1** freeze, whose reports, results tables
and configuration hashes name build `419395c8`. Everything outside those
twenty slices — the other sixty-two reports, the latency corpus, and the
Amendment A5/A9/A10 measurement records — still names the build it was
produced on, because none of it was re-run.

#### 2026-09-03 — v0.7.0 freeze-prep pin-currency survey (no declaration moved)

A survey, not a review: it records every pin's distance from upstream latest
on the day the v0.7.0 freeze-prep opened, so the bump-or-hold decision for
each analyzer is taken against a dated table rather than a guess. **No pin
was bumped and no evidence was re-run for this entry.** Pins are read from
the committed reports and adapter READMEs; upstream latest is the newest
non-draft, non-pre-release tag on the upstream release page (or PyPI where
the pin is a wheel), read on 2026-09-03.

| Analyzer | Pin (declared and witnessed) | Upstream latest stable (date) | Distance | Hold reason on record |
| --- | --- | --- | --- | --- |
| Bifrost | v0.10.8, build `419395c8066b9eddfba06aa69c8a151ef4968249` | v0.10.9 (2026-09-03) | 1 release behind | No hold reason recorded. The bump-or-hold decision is owed at this freeze-prep |
| CodeQL CLI | 2.26.4 | 2.26.4 (2026-08-26) | Current | — |
| CodeQL query packs | `java-all@9.2.3`, `python-all@7.2.3`, `javascript-all@2.9.0`, `csharp-all@7.1.2`, `go-all@7.2.3`, `cpp-all@12.0.2`, `ruby-all@6.0.3`, `rust-all@0.2.19` | Resolved by `codeql pack install` under the CLI pin | Re-resolved with the CLI at each review; unchanged at 2.26.4 | — |
| Semgrep CE | 1.175.0 | 1.176.0 (2026-09-01) | 1 release behind | No hold reason recorded |
| Semgrep rules snapshot | `semgrep/semgrep-rules@40b8c63f75dc7c22c8a77482d73bfb864b146f7e` (2026-07-30) | `develop` head is the same commit | Current — 0 commits ahead of the pin | — |
| Joern | 4.0.614 (2026-08-28) | 4.0.617 (2026-09-03) | 3 dailies behind (4.0.615, 4.0.616, 4.0.617) | The 2026-09-01 hold reason was scoped to the v0.6.1 delta and expires at this boundary; no hold reason recorded for v0.7.0 |
| OpenTaint | `analyzer/2026.08.27.17eb0fe`, by asset digest | `analyzer/2026.09.03.9752bd2` (2026-09-03) | 1 release behind | No hold reason recorded |
| Infer | v1.3.0 | v1.3.0 (2026-05-12) | Current | — |
| FlowDroid | 2.15.1, jar by digest | 2.15.1 (2026-02-23) | Current | — |
| Pysa — pyre-check | 0.10.0, wheel by digest | 0.10.0 on PyPI (2026-08-06) | Current | — |
| Pysa — Pyrefly | 1.2.0, wheel by digest | 1.2.0 (2026-08-01); 1.3.0-dev.3 is a pre-release and does not count | Current | — |

Two reading notes. The pyre-check GitHub release page stops at v0.9.23
(2024); the pin is a PyPI wheel, so PyPI is the currency source for that
row. And the Joern adapter README's "Pinned distribution" table still read
`4.0.610` at the time of this survey while every committed Joern report
witnesses `4.0.614`; that declaration is corrected in the same change as this
survey, because a declaration that disagrees with its own retained evidence
is exactly the silence this policy exists to remove.

The four rows with a gap — Bifrost, Semgrep CE, Joern, OpenTaint — each get
one of the two outcomes the policy allows at the v0.7.0 freeze-prep: a bump
with a full re-run of that adapter's slices, or a dated hold reason written
into the next review entry and repeated in the release notes.

#### 2026-09-04 — v0.7.0 freeze-prep Bifrost re-pin

The first decision taken against the 2026-09-03 survey, and a narrow one: the
Bifrost row had no hold reason on record, so by the policy above it was a
bump. The other three gapped rows — Semgrep CE, Joern, OpenTaint — are not
decided here and still owe their own bump-or-hold entries before the v0.7.0
freeze.

| Analyzer | Pin at survey | Outcome | Basis |
| --- | --- | --- | --- |
| Bifrost | v0.10.8, build `419395c8066b9eddfba06aa69c8a151ef4968249` | **Bumped to v0.10.9** | `--version` witnessed `bifrost 0.10.9` (the first line of a four-line banner, see below); `--build-identity` witnessed `04775a7b38c9c025714168328ddb8b793a326461` |

**What the bump is for.** Upstream v0.10.9 (released 2026-09-03) closes
BrokkAi/bifrost-dev #2831, the Go array-element regression the v0.10.8 bump
took rather than held, and the same re-run delivers the reconciliation
re-proof that #138 owed for all twenty Bifrost reports since PR #134 — one
re-run serves both, so the two are recorded together under
[Amendment A31](#a31--2026-09-04-the-twenty-bifrost-populations-are-re-run-on-v0109-and-every-reached-outcome-is-anchor-proven-under-sink-anchor-reconciliation).

**Which binary, and why it matters.** The pinned build is the upstream
release asset `bifrost-v0.10.9-universal-apple-darwin.tar.gz` (SHA-256
`69ae168ae8fb3a96046360b8796343ec124fc720b9e089f98a35133f3a260a96`). A
`cargo install brokk-bifrost@0.10.9` build of the same version answers
`--build-identity` with `unknown`, because the crate's build script derives
the identity from git history that a registry source does not carry; a
release-scope freeze rejects that value, so such a build cannot produce
conforming evidence. Filed upstream as BrokkAi/bifrost-dev #2998. The
witnessed `04775a7b…` is the commit the release's own identity rule names —
the last commit touching a compiled input at tag `v0.10.9` — and the same
rule, applied to `v0.10.8`, reproduces the retained `419395c8…`.

**The banner.** v0.10.9's `--version` prints four lines: the version, its two
built-in policy packs (`bifrost.code-smells@2.10.0`, `bifrost.security@1.0.0`),
and the built-in policy catalog digest
`sha256=aea2ad0c592f7252009655b62b78a884bde38c63d0b83a1e82f0db96012a797d`.
The runners witness the banner verbatim but stamp only its version line as
`tool_version` — the same line every earlier pin witnessed — and retain the
whole banner beside the raw evidence as `witnessed_tool_version_banner` in
each population's `run-environment.json`, so the shipped pack catalog the
tool-native profile activates is now a witnessed identity rather than an
inference.

**The latency corpus is not re-measured.** It stays frozen at v0.6.0 and
keeps naming v0.10.7 as the measured environment's Bifrost, under the same
rule the v0.6.1 entry states.

**This review moved declarations only; the evidence re-run followed** as
Amendment A31, on the same day, at the unchanged fixture revision.

## Challenge-tier rollout mechanics

[The challenge-tier preregistration](challenge-tier.md) fixes *what* the
thirteen additional templates are, which of them apply to each language, and
what each language's expanded core denominator becomes. It deliberately leaves
the validator work to the waves that author the fixtures. This section is the
mechanics: how a language moves from its classic denominator to its expanded one
without any population check being rewritten, and how the tiers stay separated
while only some languages have moved.

**One table.** `CHALLENGE_ROLLOUT` in `src/templates.rs` holds one row per language:
its `classic` template set (sixteen, or fifteen where the exception-catch cell
is inapplicable), the `challenge` set the preregistration's applicability matrix
assigns it, and a `rolled_out` flag. `expected_core_templates(language)` returns
`classic` while the flag is `false` and `classic + challenge` once it is `true`.
Every population check reads that function — the corpus-wide balance validator,
the Bifrost per-language kernels, the CodeQL ECMA and C-family kernels, the
Joern kernels, and the Semgrep kernels — so no denominator is stated twice.

**A wave PR flips one row.** The language PR that authors a language's challenge
fixtures sets that row's `rolled_out` to `true` in the same change. Nothing else
in the validator moves: the Bifrost run's expected core count, the CodeQL and
Joern balance checks, and the Semgrep selection all follow the row. Before the
flip, a language with no challenge fixtures validates against its classic set,
so it is never failed for lacking fixtures that do not exist yet; after the
flip, the language is required to carry the full expanded set, so a partial
fixture landing fails validation rather than silently reducing a denominator.
The `challenge` sets themselves are preregistered and are not a wave's to edit.

The per-language balance check used to compare each ECMA kernel's template set
against Java's. That comparison is gone: with the three wave-1 languages landing
in separate PRs, it would have made a language's correctness depend on which
sibling merged first. Each language now answers to its own preregistered row.

**The smoke slice is pinned by template identity, not only by policy.** The
frozen 118-case Bifrost smoke population was pinned by naming the seven policies
it evaluates. That is no longer sufficient: a challenge case names the *same*
language-kernel policy its classic siblings
name, so it would have been swept into the frozen population and quietly changed
what those 118 cases mean. `smoke_population_case` therefore refuses any case
whose `template_id` begins with `dfb-template-chal-`, whatever policy it names
and whether or not it declares an `unsupported_reason`. A regression test pins
the count at 118 and a second one asserts the refusal directly.

**Java and JavaScript have dedicated Bifrost kernels.** `run-bifrost-java-kernel`
and `run-bifrost-javascript-kernel` write `reports/bifrost-java-kernel.json` and
`reports/bifrost-javascript-kernel.json` with their own raw-evidence roots,
matching the pattern every language after Python already follows. Each selects
its language's whole core population — classic today, classic plus challenge
after the row flips — and pins the language-qualified policy for the run so all
of its assertions share one configuration hash, exactly as the Kotlin kernel
does. The frozen direct-propagation pairs keep the policies they were published
with: Java's positive and negative name `direct-positive.rqlp` and
`explicit-negative.rqlp`, JavaScript's pair names the cross-language breadth
policy, and the selector accepts all of them rather than rewriting evidence a
freeze manifest binds byte-for-byte.

Both commands have now been run against their languages' real challenge
fixtures, so `reports/bifrost-javascript-kernel.json` and
`reports/bifrost-java-kernel.json` are those languages' expanded-core Bifrost
evidence. The frozen 118-case smoke slice is untouched by either and remains
the published 32-assertion Java and JavaScript slices.

**A freeze-bound report is not re-run by the wave that expands its language.**
`reports/freeze.json` digest-binds nineteen reports, including all ten CodeQL
kernel reports and eight of the Bifrost kernel reports. Overwriting one would
invalidate a published freeze, so those adapters are deferred to the v0.4.0
freeze-prep re-run and the deferral is recorded in that language's kernel
contract. Deferral is not absence of coverage, and the v0.3.0 and v0.4.0
populations are never compared number-to-number.

**Semgrep CE's challenge partition is preregistered.** All thirteen challenge
templates are decided `unsupported` by declared capability, from the pinned
distribution's own documentation, before any challenge fixture exists. The
decision is keyed by template ID rather than by fixture tags, so no later
fixture's `feature_tags` and no observed result can move a case between the
partitions. The per-template rationale is in
[the Semgrep adapter notes](../adapters/semgrep/README.md).

**The rollout is complete. All thirteen rows are flipped** — Python,
JavaScript, Java, C#, TypeScript, Kotlin, Go, C++, C, Rust, Scala, PHP, and
Ruby — so every core kernel now carries its preregistered expanded
denominator and no language validates against its classic set alone. Ten of
the thirteen have a core
denominator of 29 templates and 58 assertions; **C++'s is 28 templates and 56
assertions**, **Rust's is 27 templates and 54 assertions**, and **C's is 24
templates and 48 assertions**, because some cells are inapplicable to those
languages — `exception-catch` from the classic sixteen for both C and Rust,
`chal-reflective-invocation` from the challenge thirteen for both C++ and
Rust, and three further challenge cells for C. An inapplicable cell reduces
only its own language's denominator. The Python wave re-ran the
adapters no freeze binds — Joern and Semgrep CE — while leaving its
freeze-bound Bifrost and CodeQL reports exactly as published; the JavaScript
and Java waves re-ran Joern and Semgrep CE too, and each additionally ran its
dedicated `run-bifrost-<language>-kernel` command, which writes a report no
freeze binds and so is not a rewrite of published evidence. The JavaScript and
Java CodeQL reports stay as published. The TypeScript wave could run **only
Semgrep CE**: both its Bifrost and its CodeQL reports are freeze-bound, so both
are deferred to the v0.4.0 re-run, and the Joern adapter has no TypeScript
slice to run at all. The Go wave is in the same position for the same reasons:
its Bifrost *and* CodeQL reports are both freeze-bound, so both are deferred to
the v0.4.0 re-run, and the Joern adapter has no Go slice — Semgrep CE was its
only runnable adapter. The per-adapter evidence, including which adapters were
deferred, is in [the Python kernel contract](python-kernel.md), [the JavaScript
adaptation matrix](javascript-kernel.md), [the Java kernel
contract](java-kernel.md), [the TypeScript adaptation
matrix](typescript-kernel.md), and [the Go kernel contract](go-kernel.md).

The Rust wave ran **Joern and Semgrep CE** over its whole expanded
54-assertion population — `reports/joern-rust-kernel.json` and
`reports/semgrep-rust-kernel.json` are both post-freeze and bind nothing — and
deferred **both** Bifrost and CodeQL, whose Rust reports are digest-bound by
v0.3.0. It is the first engine evidence on any systems language's challenge
strata; see [the Rust kernel contract](rust-kernel.md).

The C# wave ran **no adapter at all**, and that is the honest consequence of the
freeze rule rather than a gap in the wave. Every analyzer that covers C# is
either freeze-bound or absent: `reports/bifrost-csharp-kernel.json` and
`reports/codeql-csharp-kernel.json` are both digest-bound by
`reports/freeze.json`, Joern ships a `csharpsrc2cpg` frontend but this
repository has no C# Joern slice, and Semgrep CE cannot analyze C# at all
because the pinned distribution lists it as a Pro-only language. The C#
challenge fixtures, the flipped row, and the validation battery land now; all
expanded C# evidence arrives at the v0.4.0 re-run. See [the C# kernel
contract](csharp-kernel.md).

Kotlin is the sparsest case and is worth stating explicitly, because a reader
could otherwise mistake it for missing coverage. **Both** of Kotlin's
analyzer reports — `reports/bifrost-kotlin-kernel.json` and
`reports/codeql-kotlin-kernel.json` — are freeze-bound, so both adapters are
deferred to the v0.4.0 re-run; Joern has no Kotlin slice in this repository at
all (its `kotlin2cpg` frontend exists upstream and is recorded as available but
out of scope); so Semgrep CE is the only adapter this wave could run over
Kotlin's expanded population, and it did. The per-adapter evidence, including
which adapters were deferred, is in [the Python kernel
contract](python-kernel.md), [the JavaScript adaptation
matrix](javascript-kernel.md), and [the Kotlin kernel
contract](kotlin-kernel.md).

The C wave carries the most sharply **reduced** challenge set: four of the thirteen
templates are inapplicable to C, so its expanded core is 24 templates / 48
assertions rather than 29 / 58. Like TypeScript, it could run **only Semgrep
CE** — `reports/bifrost-c-kernel.json` and `reports/codeql-c-kernel.json` are
both digest-bound by `reports/freeze.json`, and the Joern adapter has no C
slice — so both engine re-runs are deferred to v0.4.0. See [the C kernel
contract](c-kernel.md).

The Ruby wave is the last of the thirteen and the opposite extreme: the only
one that defers **nothing**. Ruby's kernel landed *after* the v0.3.0 freeze, so
none of its four reports appears in `reports/freeze.json`'s report list, and all
four adapters — CodeQL, Joern, Bifrost, and Semgrep CE — were re-run whole over
the expanded 58 assertions. All thirteen of Ruby's challenge templates are
directly applicable, so its expanded core is the full 29 templates. Ruby is
therefore the only language with complete expanded-core evidence from all four
adapters, and `reports/codeql-ruby-kernel.json` is the **only CodeQL report in
this repository that reflects the challenge tier at all** — every other CodeQL
kernel is digest-bound at its 32-assertion classic population. It scores 49/58
— 29/32 classic and 20/26 challenge, clean **6/6** on stratum D, the context
and depth stress stratum. Joern scores 40/58 — 26/32 and 14/26 — and carries the
wave's one **recorded measured departure** from the challenge preregistration:
at the same pinned `maxCallDepth=4` that makes Java, JavaScript, Python, PHP,
and Rust miss the depth-6 relay positive, Ruby discriminates that pair
correctly. The departure is recorded as measured rather than reconciled to the
prediction. Semgrep CE scores 12/14 on its preregistered intraprocedural
partition with the other 44 assertions `unsupported`, and Bifrost returns 58/58
`inconclusive` under a new *taint semantic binding is unavailable* diagnostic
class rather than reporting absent flows as negatives. See [the Ruby kernel
contract](ruby-kernel.md).

With Ruby's row flipped the challenge-tier rollout is complete: all thirteen
core kernels carry their preregistered expanded denominators, and every
remaining gap is an adapter re-run deferred to v0.4.0 by the freeze rule, not a
missing fixture.

## Modeling matrix rollout mechanics

[The modeling-matrix preregistration](modeling-matrix.md) fixes *what* the
twelve benchmark-controlled modeling templates are, which of the six categories
each analyzer can express, and what a language's modeling denominator becomes.
It deliberately leaves the runner work to the pull requests that author the
fixtures and the model artifacts. This section is the mechanics, on the same
terms as the challenge-tier section above.

**Infrastructure now, fixtures and models per language.** The runner
infrastructure — the template constants, the population validator, the per-tool
partition, the four commands, the artifact-path conventions, and the
load-bearing-model gates — lands ahead of any fixture. Wave M1 then adds Java,
JavaScript, and Python one pull request at a time: that language's twenty-four
fixtures and cases, the per-adapter model encodings its partition entitles it
to, and the runs. A wave never edits a template definition or a partition cell.

**Presence is the signal; there is no rollout table.** The challenge tier needed
`CHALLENGE_ROLLOUT` because its templates *expand an existing denominator*, so
something had to say whether a language's core is the classic set or the
expanded one. Modeling is its own tier with its own denominator, so the
question does not arise: `validate_modeling_cases` in `src/modeling.rs` checks each
language that has modeling-tier cases against the preregistered twelve, and a
language with none has no modeling denominator at all — which is different from
having a zero, and validates trivially. The first fixture a language commits
turns the check on for that language, and a partial landing fails the build
rather than silently reducing a denominator.

**Tier isolation is structural, not a filter someone has to remember.** A
`dfb-template-model-` template and `score_tier: "modeling"` imply each other,
and the validator rejects a case where they disagree. Because every core,
calibration, `language-extension`, and `real-project` selection already filters
on the tier, a modeling case cannot leak into any of them; `smoke_population_case`
additionally refuses modeling cases outright, the same way it refuses challenge
ones, so the frozen 118-case Bifrost smoke population cannot absorb one.

**The partition is `CHALLENGE_SEMGREP_PARTITION` generalized across the
adapters.** `MODELING_PARTITION` holds one cell per tool per category, for
every adapter in `ModelingTool::ALL` — the preregistration's four plus each
amendment-added adapter's six, with the cells the documents mark *to be
verified* recorded as `unsupported` per their own rule and the dated
amendments applied on top as template-level overrides. No total is stated
here: the constant is a slice and the tests derive the count, so a new
adapter appends its cells without editing anyone else's. Scored today, one
line per adapter so additions compose:

- **Bifrost 4 templates of 12** (S, and Z since Amendment A9)
- **CodeQL 12 of 12**
- **Joern 8 of 12** (S, Z, E, B — Amendment A2)
- **Semgrep CE 5 of 12** (S, E, and one of Z's two templates — Amendment A3)
- **Infer 5 of 12** (S, Z, and template 3 of P — Java only, Amendment A13)
- **Pysa 10 of 12** (S, P, Z, O, E — Python only, Amendment A16)
- **FlowDroid 7 of 12** (S, P, O, and Z's kill template — Java only, Amendment A18)
- **OpenTaint 6 of 12** (S, P, Z — Java only, Amendment A22)

A declined cell is decided from the
template ID *before the tool is invoked*, retains the document's rationale
verbatim as its reason, and writes a `retained-capability-decision` evidence
document beside the report. The decision is keyed by template identity, never
by `feature_tags` and never by an observed result — a regression test asserts
the cell does not move when a case's tags are rewritten — and revising one is a
dated amendment on the preregistration, not an edit here.

**Model artifacts are conventions the language PRs populate.** One artifact per
tool per language, hash-bound into the report's `configuration_hash`:

| Adapter | Modeling artifact |
| --- | --- |
| Bifrost | `adapters/bifrost/policies/model-<language>.rqlp` |
| CodeQL | `adapters/codeql/<language>/queries/<Language>Modeling.ql`, except Java's, which is `adapters/codeql/queries/JavaModeling.ql` |
| FlowDroid | `adapters/flowdroid/summaries/model-java/` — a directory of StubDroid summary XMLs, whose three files bind the hash individually, alongside the kernel's endpoint template, wrapper template, and manifest blob (Java only; Amendment A18) |
| Infer | `adapters/infer/config/model-java.json` — Java only; the pinned distribution executes no JavaScript or Python frontend, so those combinations have no artifact and no denominator (Amendment A13) |
| Joern | `adapters/joern/semantics/model-<language>.semantics`, plus the shared `adapters/joern/queries/modeling.sc` |
| Semgrep | `adapters/semgrep/rules/model-<language>.yaml` |
| Pysa | `adapters/pysa/models/modeling-python.pysa` (Python only), plus the committed `adapters/pysa/taint.config` the kernel also binds; the runner cuts the per-template block at its `# template:` markers, because the pinned pair refuses a model naming a definition the case's sources do not carry |
| OpenTaint | `adapters/opentaint/rules/model-java.yaml` (Java only, Amendment A22) |

The CodeQL path departs from the preregistration's schematic
`adapters/codeql/queries/<Language>Modeling.ql` and sits inside that language's
existing `qlpack`, because a query outside a pack cannot resolve its
`codeql/<language>-all` dependency. That is a location, not a declaration
surface: the document's `ConfigSig` encoding is unchanged. Java is the one
language for which the schematic path is already correct, because Java's pack
*is* the adapter root — `adapters/codeql/qlpack.yml` declares
`dataflowbench/codeql-java` and `JavaKernel.ql` sits beside it — so there is no
`adapters/codeql/java/` to descend into and a query under one would resolve
nothing. Joern is the one adapter with two files, and both bind the
configuration hash.

**One command per adapter, parameterized by language** — listed one per line
so a new adapter's line composes without editing the others. Each takes
`--language java|javascript|python` and writes
`reports/<tool>-<language>-modeling.json` with raw evidence under
`reports/raw/<tool>-<language>-modeling/`:

- `run-bifrost-modeling`
- `run-codeql-modeling`
- `run-joern-modeling`
- `run-semgrep-modeling`
- `run-infer-modeling` (Java alone)
- `run-pysa-modeling` (Python alone; its identity is the witnessed
  pyre-check + Pyrefly pair, so it takes the kernel's
  `--pyre`/`--pyre-binary`/`--pyrefly` instead of one binary path)
- `run-flowdroid-modeling` (Java alone, on the kernel's jar toolchain —
  Amendment A18)
- `run-opentaint-modeling` (Java alone; takes the pinned release assets
  instead of a binary, witnessing their digests before any case runs, exactly
  as the OpenTaint kernels do — Amendment A22)

The per-language *kernel* commands
are separate commands because each language's kernel differs in real toolchain
plumbing — a `kotlinc` trace, a `go build`, a synthesized Cargo crate, a
different extractor. A modeling run has none of that: three languages, three
already-wired toolchains, and a run that differs from its sibling only in which
artifact it loads and which population it selects. A `--language` argument says
that once instead of twelve times. `run-infer-modeling` and
`run-opentaint-modeling` accept Java alone — the other two languages have no
Infer or OpenTaint denominator, and the runners refuse them rather than
writing an empty report.

**Fail fast, never an empty report.** A run refuses, before touching the
analyzer, when:

- the language has no modeling population — *"no modeling population for
  `<language>`"*, because a report over zero assertions asserts nothing;
- the tool's modeling artifact for that language is missing or unreadable. This
  is the preregistration's *missing model* arm: a scored cell with no
  declaration behind it is a defect in DataFlowBench, not evidence about the
  analyzer, so it is a **hard error** that fails the build and never an
  outcome — not `unsupported`, not `not-reached`, not a result;
- a `--codeql-packs` search path is named but does not exist.

**The load-bearing-model gates are wired now so a language PR cannot forget
them.** A modeling assertion is only evidence of activation if the tool's
behavior *without* the model would differ, and two adapters have an
unmodeled-call default that would otherwise decide category P and O cells on
their own. So the runner reads each artifact before the run and refuses it
unless the default is disabled: a Bifrost modeling policy must set
`:call-modeling (call-modeling :unmodeled require-model)` and must not name the
kernel policies' `optimistic`, and a Semgrep modeling rule must set `options:
taint_assume_safe_functions: true`, and every `TaintInTaintOut` in the Pysa
modeling artifact must sit under `@SkipAnalysis` + `@SkipObscure` — Amendment
A16 measured the pinned pair resolving the matrix's reflective body on its
own, so without the skip modes the engine's body reading would decide the
category P and O cells. Tests pin all three gates. CodeQL has no
such switch to pin — a `ConfigSig` with no `isAdditionalFlowStep` adds no
step. Infer has no unmodeled-call default to pin either — where a body is
captured, Pulse reads it — but its configuration surface has silent-failure
shapes of its own, and `require_infer_modeling_load_bearing` refuses each of
them (Amendment A13). OpenTaint needs no switch and no gate: the surface
probe behind Amendment A18 measured that with no propagator declared the
pinned engine carries nothing through an unfollowable body, so it is
`require-model`-shaped out of the box. Joern's equivalent claim ("a method
with no `FlowMapping` propagates nothing") was measured false by the first
wave-M1 run: `FlowSemantic`
mappings on the pinned 4.0.610 are additive over the engine's default
pass-through, which is why Amendment A2 moved Joern's propagator and summary
categories to unsupported activation rather than gating them.

**The execution arm lands with the language.** The arm that invokes an
analyzer over a *scored* cell is written by the pull request that authors that
adapter's declarations for that language. All three of wave M1's languages are
wired on the same four runners: Python (`docs/python-modeling.md`), JavaScript
(`docs/javascript-modeling.md`), and Java (`docs/java-modeling.md`); the
amendment-added adapters' arms — Infer (A13), Pysa (A16), FlowDroid (A18),
OpenTaint (A22) — each landed in the same pull request as their
declarations, per the same rule. Wave M1 is therefore
complete, and a scored cell in a language that has no arm stays a hard
error rather than a synthesized outcome, which the adapter contract at the head
of this document forbids. The `unsupported` arm is independent of all of that,
so a tool that declines every category a population carries produces a whole,
validated report of retained capability decisions without the analyzer being
invoked at all.

**Reconciliation on this tier is source-anchored as well as sink-anchored,** and
that is a property of the fixtures rather than of any adapter. A modeling fixture
carries both halves of its pair in one type — the declared entity and its
undeclared sibling — because that is what the templates say makes the negative a
negative, and category E's handlers need no caller, so the declared handler's
flow is present in the negative's fixture too. A finding therefore counts only
when it lies in the region its case's own source anchor governs *and* on a
callsite of its anchored sink function. An unmatched finding on this tier is the
pair's other entity, fully attributable, so it normalizes to `not-reached` with
the count retained — not to the kernels' `inconclusive`, which is reserved here
for evidence with no usable location at all.

**Reporting stays separate.** Modeling reports are their own population per
language and per adapter, bound into a freeze manifest like every other report,
ordered on generated scorecards by the `modeling` entry in `SCORE_TIER_ORDER`.
A modeling assertion never appears on a propagation-kernel scorecard, never
enters a core denominator, and is never macro-averaged with one.

## Tool-native rollout mechanics

[The tool-native preregistration](native-profile.md) fixes *what* the six
platform-API templates are, what each tool's activation contract pins, and which
cells each tool can activate at all. This section is the mechanics, on the same
terms as the two sections above.

**Infrastructure now, fixtures and vendored snapshots per language.** The
template constants, the category mapping, the activation partition, the
profile-disjoint validators, the four commands, the activation shapes, and the
gates land ahead of any fixture. Wave N1 then adds Java, JavaScript, and Python
one pull request at a time: that language's twelve fixtures and cases, the
vendored activation snapshots its partition needs, and the runs.

**One tier, two profiles, and the selectors say which.** Native cases carry
`score_tier: "modeling"` and `model_profile: "tool-native"`. The tier keeps both
modeling populations out of every core, calibration, `language-extension`, and
`real-project` denominator; the *profile* is what keeps them out of each other,
so `modeling_case` and `native_case` both filter on it and
`validate_profile_disjoint_populations` asserts corpus-wide that no case is
selected by both, in either direction, for any language. That check exists
because pooling the profiles is a fault of omission — a selector that filters on
the tier and forgets the profile — which no assertion about a case's own fields
would catch.

**The partition is keyed by template, not by category — and, since
[Amendment N-A1](native-profile.md#n-a1--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension),
by language too.** `NATIVE_PARTITION` holds one cell per tool per template —
one cell per tool per template for every adapter in `ModelingTool::ALL`,
transcribed from the preregistration's summary and the dated amendments that
added the later rows — Infer's by
[Amendment A14](native-profile.md#a14--2026-09-01-infers-native-row-declines-on-a-measured-silence)
(declined on a measured silence), Pysa's by
[Amendment A17](native-profile.md#a17--2026-09-01-pysa-joins-the-tool-native-profile-with-a-live-activation-row),
FlowDroid's by Amendment A19 (declined on the shipped catalog's text,
re-grounded on the shipped surface's full enumeration and executed
engagement by
[Amendment A29](native-profile.md#a29--2026-09-02-flowdroids-native-decline-is-re-grounded-on-the-shipped-surfaces-full-enumeration-and-executed-engagement)), and
OpenTaint's by
[Amendment A23](native-profile.md#a23--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product)
— with the *to be verified* cells recorded as `unsupported` per the documents'
own rule (no total is stated here; the constant is a slice and the tests
derive the count) — and
`NATIVE_PARTITION_AMENDMENTS` sits in front of it with one row per amended
tool × language × template. The language dimension exists because a vendored
activation snapshot is per language: reading Python's rules can only answer
Python's cells, and a partition without a language could not say so. As
preregistered: **CodeQL 6 templates of 6**, and **Bifrost, Joern, and Semgrep
CE 0 of 6**. As amended, one line per adapter so additions compose:

- **Semgrep CE 6 of 6 for Python** (Amendment A8, on the evidence of its
  vendored snapshot; unchanged elsewhere)
- **Infer 0 of 6 for Java** (Amendment A14, a measured silence of the shipped
  Pulse checker; the other languages have no Infer native denominator at all)
- **Pysa 6 of 6 for Python** (Amendment A17, over the taint model suite the
  pinned pyre-check wheel ships in `lib/pyre_check/taint/`, activated with
  `--no-verify` and guarded by the retained-evidence proof that the shipped
  `os.system` sink model bound)
- **FlowDroid 0 of 6 for Java** (Amendment A19, with a live activation
  contract — the shipped `SourcesAndSinks.txt` catalog and default summary
  wrapper from inside the pinned jar — whose catalog binds no identity any
  native template uses)
- **OpenTaint 0 of 6 for Java** (Amendment A22 — its shipped models archive
  is propagation without endpoints, and the pinned release ships no rule set)

The asymmetry with the
benchmark-controlled matrix is the point rather than a defect — Joern scores four
of six categories there on the same engine — because this profile measures
product packaging and that one measures the engine. A declined cell is decided
from the template ID *before the tool is invoked*, retains the document's
rationale verbatim, and writes a `retained-capability-decision` document beside
the report carrying the pinned activation configuration with it.

**One command per adapter, parameterized by language** — listed one per line
so a new adapter's line composes without editing the others. Each takes
`--language java|javascript|python` and writes
`reports/<tool>-<language>-native.json` with raw evidence under
`reports/raw/<tool>-<language>-native/`:

- `run-bifrost-native`
- `run-codeql-native`
- `run-joern-native`
- `run-semgrep-native`
- `run-infer-native` (Java alone — the pinned distribution executes no
  JavaScript or Python frontend, so those languages have no Infer native
  denominator, Amendment A14)
- `run-pysa-native` (Python alone, pair-witnessed like its modeling sibling)
- `run-flowdroid-native` (Java alone, witnessing the pinned jar and platform
  digests before writing its twelve retained decisions — Amendment A19)
- `run-opentaint-native` (Java alone; takes the pinned release assets instead
  of a binary — its partition declines every cell, and the run still
  witnesses both assets' digests, because a report whose whole evidence is
  retained rationales must name a measured identity — Amendment A23)

**Fail fast, never an empty report.** A run refuses, before touching the
analyzer, when the language has no tool-native population, when a pinned
activation artifact is missing — this profile's analogue of the modeling
matrix's *missing model*, and a hard error for the same reason — or when a named
`--codeql-packs` path does not exist.

**The no-benchmark-models gate is the profile's load-bearing check.** A native
run must supply no benchmark-authored model of any kind, so the runner reads the
pinned activation shape and refuses it if any argument names a benchmark model
artifact. The artifact set is derived from the modeling matrix's own constants —
every `ModelingLanguage::artifact` for every tool, plus
`adapters/joern/queries/modeling.sc` — so a modeling artifact added later is
covered the moment it is declared. Tests pin every activation shape literally:
`--threat-model=local` plus the shipped `<language>-security-extended.qls` suite
for CodeQL, `--oss-only` plus `--config=adapters/semgrep/native/<language>` for
Semgrep, `--policy-pack` and never `--policy-file` for Bifrost, nothing at
all for Joern, which activates `DefaultSemantics` by running,
`--pulse-only` with no `--pulse-taint-config` for Infer, whose shipped taint
analysis is off absent one — the measured silence Amendment A14 declines on —
`-s` pointed at the catalog extracted verbatim from FlowDroid's own pinned
jar, which is why that row vendors nothing (the jar digest is the
provenance), and the shipped models archive's flags and never
`--semgrep-rule-set` for OpenTaint, whose archive is shipped product
(Amendment A23) while the rule set is where a benchmark-authored endpoint
would arrive.

**Activation configuration binds the configuration hash.** Most of a native
run's configuration is not a file in this repository — it is a suite name, a
pack version, a threat-model group — so `native_configuration_hash` hashes the
pinned activation identity and arguments alongside whatever vendored bytes
exist. That is what makes issue #16's *"model/version provenance and activation
configuration are retained"* a property of the artifact.

**Vendored activation artifacts carry `derived` provenance.** Where shipped
models are not pinnable at run time — Semgrep's registry, most prominently;
Joern's `querydb` was cited here until Amendment A26 measured that its
release asset is versioned and pinnable after all — the profile vendors a
pinned snapshot with a
`provenance.json` recording the upstream repository, source commit, paths,
license, and retrieval date. Wave N1 vendored all three:
`adapters/semgrep/native/javascript/` (thirty rules),
`adapters/semgrep/native/java/` (eighty-six), and
`adapters/semgrep/native/python/` (ninety-one), all from
`semgrep/semgrep-rules@40b8c63f`, each with a per-file digest so the report's
`configuration_hash` binds the rules and not just the manifest.

**One execution arm serves every language.** The arm that invokes an analyzer
over a *scored* native cell is written by the wave-N1 pull request that first
needs it, and thereafter every language shares it. CodeQL's arm is wired:
`run_codeql_native_case` calls the same `codeql_sarif_for_case` driver the
kernels and the modeling matrix call, so the database is built by the
language's own extractor and traced build — extraction is a property of the
language, not of the model profile — and the failure evidence and scratch
cleanup are the shared ones. Only two things are native, and both are arguments
to that driver rather than a second copy of it: the pinned activation arguments,
passed verbatim in the order `native_activation` pins and
`native_configuration_hash` hashes so the invocation and the retained provenance
cannot drift apart, and the reconciler. The `--codeql-packs` search path is
validated but deliberately never forwarded, because a pack search path of ours
is a model of ours.

Semgrep's arm is wired too, by the Python row, because
[Amendment A8](native-profile.md#a8--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension)
promoted that language's six cells to scored and the preregistration's rule is
that a promotion lands its runner in the same pull request. It is not a second
reconciler: `run_semgrep_native_case` classifies its findings against the same
`native_sink_anchor_locations` anchors and tallies them through the same
`native_anchor_tally_outcome` the CodeQL arm reaches, so the two adapters cannot
drift into two readings of the outcome vocabulary. It stays unreachable for
JavaScript and Java, whose Semgrep cells the partition still declines.

Bifrost and Joern have no arm, because their preregistered partitions decline
all six templates for every language and the partition is consulted first; a
scored cell for one of them is a hard error rather than a synthesized outcome,
which the adapter contract at the head of this document forbids, and it becomes
reachable only when a dated amendment promotes a cell.

**Native anchoring binds a callsite, not a declaration.** Every other population
here puts a `DFB-SINK:` marker on the declaration of a benchmark-invented
endpoint and reconciles against that function's callsites. A native fixture
declares no endpoint — the sink's body is inside the platform — so the marker
sits on the real platform-API callsite and `native_sink_anchor_locations`
resolves that line directly. An anchor still decides only which finding belongs
to which assertion and never tells an analyzer what a source or a sink is.

A native run also analyzes a whole shipped suite rather than one adapter query,
so a finding away from the anchor is a different query answering a different
question. It is retained as a diagnostic and never becomes evidence of a flow,
and a cell with only such findings — or with no finding at all — is a plain
`not-reached`: a coverage miss by an activated model set, which calling it
incomplete would quietly remove from the vendor's denominator. Only genuinely
unreadable evidence, or a finding matching two anchors at once, is
`inconclusive`.

**Reporting stays separate.** Native reports are their own population per
language and per adapter. A native scorecard is never merged with a
benchmark-controlled one, even though the two share a score tier and a language,
and no aggregate combines native coverage with controlled accuracy.

## Analyzers evaluated and not adapted

An adapter admits an analyzer only when four bounds hold, and every analyzer
we evaluate is recorded here against them so absence is never ambiguous:

1. **Semantic data flow.** The tool performs taint or value-flow analysis —
   the track this benchmark scores. Linters and rule/AST matchers without a
   flow engine would take a near-blanket `unsupported` and add no signal.
2. **Local, pinnable execution.** Analysis runs on this machine from an
   exactly pinned version, so evidence is reproducible. Cloud-submission
   services fail this bound even when the engine is real.
3. **Retained native output.** Machine-readable findings (SARIF/JSON) the
   runner can retain verbatim as raw evidence.
4. **Publishable results.** The license or terms of service must permit
   running the tool against a benchmark and publishing the outcome.
   Commercial SAST terms commonly restrict comparative publication; any such
   restriction is disqualifying until explicit permission exists, and we do
   not test first and ask later.

### Evaluated (2026-08, from the field surveyed in Sourcegraph's
"12 Best Static Code Analysis Tools in 2026" and our own review)

| Analyzer | Verdict | Bound(s) failed |
| --- | --- | --- |
| Semgrep CE | **Adapted** | — (bounded to its documented intraprocedural profile) |
| CodeQL | **Adapted** | — |
| OpenTaint | **Adapted** (2026-08 field evaluation) | — (JVM bytecode only, so Java and Kotlin are its two populations; pinned by release-asset digest because the analyzer self-reports no version; see [the OpenTaint adapter notes](../adapters/opentaint/README.md)) |
| Infer | **Adapted** (2026-08 field evaluation) | — (C, C++, and Java are its three populations; the pinned v1.3.0 ships no Quandary checker, so Pulse's taint configuration is the operable taint mode, verified by probe; see [the Infer adapter notes](../adapters/infer/README.md)) |
| FlowDroid | **Adapted** (2026-08 field evaluation) | — (Java and Kotlin are its two populations; the pinned 2.15.1 CLI is APK-only, verified against the binary, and the field question was whether per-case APK materialization stays within the bounds — it does, from pinned JVM-only pieces with no Android SDK dependency; see [the FlowDroid adapter notes](../adapters/flowdroid/README.md)) |
| Pysa | **Adapted** (2026-08 field evaluation) | — (Python is its one population; the pin is the pyre-check 0.10.0 / Pyrefly 1.2.0 pair, because the pinned client drives the separately released front end and the pair's one verified silent-failure mode — unresolved call graphs without a project declaration — is guarded per run; see [the Pysa adapter notes](../adapters/pysa/README.md)) |
| Snyk Code | Not eligible | (2) analysis is cloud-backed and account-bound; (4) terms to be verified but commonly restrictive — both must clear before any attempt |
| Coverity | Not eligible | (2) no free local pinned CLI (Coverity Scan is cloud submission); (4) benchmark restrictions |
| Checkmarx | Not eligible | (2) and (4) — enterprise-only, no local CLI, standard no-benchmark terms |
| Veracode | Not eligible | (2) and (4) — same class |
| Fortify | Not eligible | (2) and (4) — same class |
| SonarQube | Not eligible for the taint track | taint/injection analysis is a commercial-edition feature; the open Community engine has no cross-procedure taint, so (1) fails for the open build and (4) for the commercial one |
| Qodana | Not eligible for the taint track | taint lives in the commercial Ultimate tier; same split as SonarQube |
| PMD | Not eligible | (1) — rule/AST analysis; its historical DFA module is deprecated, no taint engine |
| ESLint | Not eligible | (1) — linter; plugins add patterns, not flow analysis |
| CodeScene | Not eligible | (1) — behavioral/hotspot analysis, not data flow |

The SonarQube and Qodana rows are coverage facts of the same shape as
Semgrep CE's C# cell: the open tier genuinely cannot analyze the track, and
that is recorded rather than tested around.

### Queued candidates that do qualify

**The queue is empty.** Every engine issue #82 queued has now cleared its
field evaluation — all four bounds held in every case, verified by probe
rather than prospectus — and is adapted above: OpenTaint (formerly issue
#17), Infer, FlowDroid, and finally Pysa. Each evaluation earned its pin
against the binary rather than the prospectus: Infer's pinned release had
removed the taint checker the issue named it for, so the operable surface —
Pulse's taint configuration — was established before any population ran;
FlowDroid's released CLI turned out to analyze APKs only, so what was
established was that a minimal per-case APK is materializable from pinned,
JVM-only pieces without changing what is measured; and Pysa's pinned client
turned out to require a second, separately released binary — the Pyrefly
front end — whose absence of a project declaration silently unresolves every
call, so the pin became a version pair and the silent mode a guarded part of
the invocation. A future candidate enters this queue by the same rule:
pinned version, probe-verified taint mode, and a partition preregistered
from documentation before any result exists.

## CodeQL language populations

The CodeQL adapter keeps Java and JavaScript as separate populations. The
JavaScript command selects that language's whole core `taint` population —
32 assertions classically, and 58 now that JavaScript's challenge row is
rolled out:

```text
language == "javascript"
track == "taint"
score_tier == "core"
tool_model_references.codeql.query ==
  "adapters/codeql/javascript/queries/JavaScriptKernel.ql"
```

The selection is balanced: one positive and one negative case for each shared
template ID — the 16 classic templates, plus the 13 challenge templates
[the challenge tier](challenge-tier.md) classifies as applicable to
JavaScript. `reports/codeql-javascript-kernel.json` is digest-bound by the
v0.3.0 freeze, so it still holds the 32-assertion classic evidence and is not
rewritten by the JavaScript expansion; the expanded CodeQL evidence is
deferred to the v0.4.0 freeze-prep re-run, as recorded in
[the JavaScript kernel contract](javascript-kernel.md). It does not select
TypeScript cases, even where CodeQL
uses shared JavaScript/TypeScript libraries. JavaScript has its own query,
pack manifest (`adapters/codeql/javascript/qlpack.yml`),
normalized report (`reports/codeql-javascript-kernel.json`), and raw SARIF
directory (`reports/raw/codeql-javascript/`). Java uses its existing query,
report, and evidence directory independently.

For each JavaScript case, the runner materializes the declared fixture files in
an isolated workspace, creates a fresh CodeQL database with the JavaScript
extractor, runs `JavaScriptKernel.ql`, and removes temporary database/workspace
artifacts after retaining the raw output. The normalized report records the
exact CodeQL CLI version/build and configuration hash observed by that run. The
retained snapshot used CodeQL CLI 2.26.3, build SHA
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with official `github/codeql` tag
`codeql-cli/v2.26.3` at source commit
`44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`. Its JavaScript pack is
`codeql/javascript-all@2.9.0` with the committed lock. Registry retrieval of
that 2.9.0 pack was unavailable in the test environment, so reproduction used
the matching official source workspace root via `--codeql-packs` (or an
equivalent matching bundle pack root):

```bash
CODEQL=/path/to/codeql-v2.26.3/codeql
CODEQL_SOURCE_ROOT=/private/tmp/codeql-source-v2.26.3
cargo run -- run-codeql-javascript-kernel \
  --codeql "$CODEQL" \
  --codeql-packs "$CODEQL_SOURCE_ROOT"
```

SARIF findings are mapped back to the benchmark's sink anchors, while the
query path evidence identifies the source-to-sink flow and normalized results
retain both anchor sets. A `DFB-SINK:` marker identifies the anchored sink
declaration/function. The SARIF result must be in the same anchor file at the
callsite to that sink identity; it need not be on the marker's exact line.
Only anchor-backed evidence contributes to `reached`; successful execution
with no matching finding contributes to `not-reached`. Unresolved or
incomplete evidence remains `inconclusive`, capability exclusions remain
`unsupported`, and database/query/parse failures remain `runner-error`. All
raw SARIF and runner diagnostics remain available for audit.

The retained JavaScript snapshot has 32 results: 15 `reached`, 17
`not-reached`, and zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. Twenty-nine of 32 match expected polarity. The false negatives are
`dfb-taint-javascript-alias-propagation-positive` and
`dfb-taint-javascript-expression-positive`; the false positive is
`dfb-taint-javascript-loop-carried-negative`. It retains 32 SARIF files, zero
error files, and empty normalized `witness_checkpoints` for every case. The
configuration hash is
`a038e39eb93d6fc674ab59cf2e4de5b3608f1d7b294c19da75ce1bd041c75ac5`.

The direct-flow breadth run, Java kernel run, JavaScript kernel evidence, and
Python kernel run are distinct adapter populations. A kernel command must
select only its language and retain the exact raw output for those cases; it
must not use a direct-flow result or a Java result as a proxy for JavaScript.
The Python kernel's template balance and construct adaptations — sixteen
templates in v0.3.0, twenty-nine once its challenge row was rolled out — are
defined in the [Python kernel contract](python-kernel.md).

### CodeQL Python slice

The Python CodeQL command selects exactly the `core` taint cases in
`cases/taint/python/`: one positive and one negative assertion for each of the
balanced template IDs in Python's core denominator — 32 assertions over 16
templates before the challenge rollout, and **58 assertions over 29 templates**
now that Python's `CHALLENGE_ROLLOUT` row is flipped. Each case's
`tool_model_references.codeql.query`
must point to `adapters/codeql/python/queries/PythonKernel.ql`; Java cases and the
13-language direct-flow baseline are excluded. The command creates a fresh
Python database per case and writes `reports/codeql-python-kernel.json` plus
one retained raw SARIF or runner-error artifact per selected case under
`reports/raw/codeql-python-kernel/`.

The Java and Python query packs are separate: Java uses the pack rooted at
`adapters/codeql/`, while Python uses `adapters/codeql/python/`, including its
language-specific database-schema dependency. Installing or resolving one
pack must not silently substitute the other language's pack.

Reproduce it with CodeQL CLI v2.26.4 and the pinned Python pack
`codeql/python-all@7.2.3`:

```bash
codeql pack install adapters/codeql/python --search-path /path/to/codeql-packs
codeql pack ls adapters/codeql/python --search-path /path/to/codeql-packs
cargo run -- run-codeql-python-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The normalized result copies the case's source and sink anchors and uses the
SARIF finding/diagnostic evidence to classify the anchored assertion. The
adapter retains `reached`, `not-reached`, `inconclusive`, `unsupported`, and
`runner-error` distinctly: incomplete or failed analysis is never a negative
result, and raw SARIF is retained even when normalization cannot complete.
The validated Python run used CodeQL CLI 2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/python-all@7.2.3`. Its 32 results are 14 `reached` and 18
`not-reached`, with no `inconclusive`, `unsupported`, or `runner-error`
outcomes; 28/32 match the expected polarity. The mismatches are false
negatives for `alias-propagation-positive`, `array-element-positive`, and
`exception-catch-positive`, and a false positive for `loop-carried-negative`.
These results cover only the Python core kernel.

`reports/codeql-python-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so the Python challenge wave did
**not** re-run it: those 32 results describe the 16-template v0.3.0 population
and are left exactly as frozen. CodeQL evidence for Python's expanded
58-assertion core arrives with the v0.4.0 freeze-prep re-run. See
[the Python kernel contract](python-kernel.md).

## Joern language populations

The Joern adapter keeps Java, JavaScript, Python, Ruby, PHP, and Rust as six
separate populations. Each command selects that language's core `taint` cases
runner-side:

```text
language == "java" | "javascript" | "python" | "ruby" | "php" | "rust"
track == "taint"
score_tier == "core"
```

The v0.3.0 freeze digest-binds every `case.json` and fixture byte, so no case
declares a Joern model reference; the per-language invocation is pinned in the
runner instead, the way the Kotlin Bifrost run pins its policy. Three of the
selections are 16 templates with one positive and one negative assertion — 32
assertions — under one model profile; Rust's exception-catch cell is
inapplicable, so its core selection is the other 15 templates, 30 assertions,
and its `Result`/`?` `language-extension` pair is not selected. Python and
JavaScript move the other way: both challenge-tier rows are rolled out, so each
core selection is the expanded 29 templates, **58 assertions**, and each was
re-run whole. The six are
disjoint. Each has its own report (`reports/joern-<language>-kernel.json`) and
its own retained-evidence root (`reports/raw/joern-<language>-kernel/`).

One committed CPG query script, `adapters/joern/queries/kernel.sc`, serves all
six. It is parameterized by the benchmark-controlled source and sink
identifiers the runner reads out of each fixture's own `DFB-SOURCE:` and
`DFB-SINK:` marker lines, and runs a single `sinks.reachableByFlows(sources)`
under the OSS data-flow engine. There is no per-case, per-template, or
per-polarity branching, and Joern's own default source/sink models are not
used. Flow evidence is reconciled against the case's anchored sink callsites; a
frontend or engine failure is `runner-error`, missing or ambiguous location
evidence is `inconclusive`, and neither can become `not-reached`. Languages
whose frontend is absent from the pinned distribution are recorded as
explicitly unsupported rather than as failures.

Rust is the one language whose fixture cannot be handed to its frontend as a
loose file: `rust2cpg` walks a Cargo crate, and given a bare `.rs` file it
produces an empty CPG. The runner therefore synthesizes a minimal `Cargo.toml`
in each case's temporary workspace, with the binary target pointed straight at
the fixture rather than at a generated `src/main.rs`. Nothing is written beside
a fixture, no case's declared file list changes, and every location Joern
reports stays on the case's own anchor filename. The pinned distribution is the
first Joern release to ship `rust2cpg` at all; the adapter records what that
frontend does today rather than treating it as settled. See the
[Joern adapter notes](../adapters/joern/README.md) for the pinned version,
frontend coverage, model assumptions, and the observed per-language results.

## Semgrep CE language populations

The Semgrep adapter keeps Java, JavaScript, TypeScript, Python, Go, Ruby, PHP,
Kotlin, Rust, C, and C++ as eleven separate populations. Each command selects
that language's whole core `taint` population runner-side by language, track,
and score tier, exactly as the Joern kernels do, and each has its own report
(`reports/semgrep-<language>-kernel.json`) and its own retained-evidence root
(`reports/raw/semgrep-<language>-kernel/`). No case declares a Semgrep model
reference: the v0.3.0 freeze digest-binds every `case.json` byte, so the
invocation is pinned in the runner instead.

Every one of the eleven now selects its expanded core, the Ruby row having been
the last to flip. **Java, JavaScript, TypeScript, Python, Go, Kotlin, PHP, and
Ruby select 58** each, their expanded 29-template cores, **C++ selects 56**,
**Rust selects
54** and **C selects 48** — 622 selected assertions in all; every one of their
challenge assertions falls in the
`unsupported` partition, so each scored subset is the same 14 as everyone
else's. **C and Rust have 15-template classic halves**: their
exception-catch cell is inapplicable in `applicability-matrix.md`, so they are
balance-checked against the fifteen-template
`KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH` set the CodeQL and Bifrost C and
Rust kernels already use; Rust's expanded core is 27 templates (15 classic plus
12 challenge) and C's is 24 (15 plus 9), both reduced denominators being
inapplicable cells that reduce only that language's own count. The
`score_tier == "core"` filter keeps C's
error-code-return and goto-cleanup cases and Rust's `Result`/`?` pair — all
`language-extension` — out of the core denominator.

Four front ends are not GA in the pinned distribution. Its shipped
`semgrep_interfaces/lang.json` records `kotlin` at `beta` and `rust`, `c`, and
`cpp` at `alpha`; the other seven are `ga`. The label is retained on the first
`diagnostics` entry of every normalized result and in every capability-decision
document, the way the CodeQL adapter records its Rust extractor's public preview
status, and it is never an input to the partition: `semgrep_capability_exclusion`
reads only `feature_tags` and `expected_analysis_capability`, so it cannot see a
language. Taint mode was verified to function on all four before they were wired
up.

Semgrep CE is the one adapter here whose scored population is a strict subset of
its selected population, and that subset is defined by documentation rather than
by results. The pinned CLI's own `semgrep scan --help` sells interprocedural
taint (`--pro-intrafile`), cross-file taint (`--pro`), and path sensitivity
(`--pro-path-sensitive`) as Pro Engine features, and the bundled `CHANGELOG.md`
records CE's heap support as "Experimental support for basic field-sensitive
taint tracking" with index sensitivity and inter-procedural field sensitivity
both marked Pro. The scored profile is therefore intra-file, intraprocedural,
flow-sensitive, path-insensitive taint — that is, the `intraprocedural`
partition of each kernel: 7 templates and 14 assertions.

The remaining templates — the `interprocedural-one-hop`,
`interprocedural-deep`, and `heap-access-path` partitions, 18 assertions in a
16-template kernel, 34 in the expanded 24-template C kernel, 40 in the
expanded 27-template Rust kernel, 42 in the expanded 28-template C++ kernel,
and 44 in each of the expanded 29-template Java, Python, JavaScript,
TypeScript, Kotlin, and Go kernels, whose challenge
templates are all outside the profile — are `unsupported`. That decision is
taken from each case's own `feature_tags` and
`expected_analysis_capability.kind` *before* Semgrep is invoked, so an
out-of-profile case never reaches a Semgrep process and cannot produce an empty
finding list that later reads as a false negative. Each retains a
capability-decision document naming the documented boundary it falls outside.
The whole selection is still balance-checked by the same
`validate_kernel_population_with` every other kernel uses, against that
language's own template set; the bounded profile narrows what is scored, never
what is selected. The scored subset is 14 assertions in all eleven languages,
because every intraprocedural template is applicable everywhere — and it stays
14 in a language whose challenge tier has rolled out, because no challenge
template carries the `intraprocedural` tag.

Rules are benchmark-controlled and committed under `adapters/semgrep/rules/`,
one `mode: taint` rule per language. Because endpoint identifiers vary per
fixture, each rule carries `__DFB_SOURCE__`/`__DFB_SINK__` placeholders that the
runner resolves per case from that fixture's own `DFB-SOURCE:` and `DFB-SINK:`
marker lines — the same resolver the Joern kernels use. Every report's
`configuration_hash` is a SHA-256 over all eleven committed rule files, so
adding the four new ones invalidated the seven existing reports and all eleven
kernels were re-run rather than four being appended beside a stale hash. The
exact resolved rule each case was analyzed under is retained beside its finding
document. `--metrics=off` and `--oss-only` are passed on every invocation, and a
finding reporting any engine other than `OSS` is a `runner-error` rather than a
data point. Issue #15 will later formalize a cross-tool taint-modeling matrix;
these rules are the endpoint-contract instantiation of it.

Semgrep's native `--json` document is the retained raw evidence, one per scored
case. Findings are reconciled against the case's anchored sink callsites: only
anchor-backed evidence is `reached`, a clean scan of the fixture with no finding
is `not-reached`, and a non-zero exit, a non-empty `errors` array, a skipped
rule, or unparseable output is `runner-error`. `raw_special_outcome` — the
freeze's raw-evidence guard — now also refuses a Semgrep document whose `errors`
array is non-empty, so a failed scan's well-formed empty `results` list can
never be frozen next to a clean negative.

All eleven kernels ran on Semgrep CE 1.174.0 (`semgrep-oss:1.174.0`, Homebrew).
Each produced 9 `reached`, 5 `not-reached`, and its whole remainder
`unsupported` — 18 each for the two unexpanded 16-template PHP and Ruby
kernels, 34 for the expanded C kernel, 40 for the expanded Rust kernel, 42 for
the expanded C++ kernel, and 44 each for the expanded Java, Python,
JavaScript, TypeScript, Kotlin, and Go kernels — with
zero `inconclusive` and zero `runner-error` outcomes, and 12/14 of each scored
subset matching the expected polarity. Every intraprocedural positive is
`reached` in every language; the two mismatches, identical in all eleven, are
false positives on `infeasible-branch-negative` and `loop-carried-negative` —
precisely the path sensitivity the pinned CLI documents as Pro-only. The four
non-GA front ends score exactly what the seven GA ones score, which says the
mismatch belongs to the shared engine rather than to any parser; it is not a
general claim about those parsers, since the scored partition exercises only
local propagation inside one function.

C# is named in that CLI's own `--pro-languages` text and so cannot be run under
CE at all — a tool limitation, permanent under the current pin. **Scala is
different in kind**: the pinned distribution records `scala` at `ga`, more
mature than three of the four languages just added, and nothing in the engine
blocks it. It is left recorded-only because the maintainer scoped it out, and
that is written down so its absence is never read as a Semgrep limitation. See
the [Semgrep adapter notes](../adapters/semgrep/README.md) for the pinned
version, the documented-scope and maturity citations, the per-language
partition, and the model assumptions.

## OpenTaint language populations

The OpenTaint adapter keeps Java and Kotlin as two separate populations —
the two languages the pinned JVM-bytecode analyzer actually executes, verified
in the field before adaptation. Each command selects that language's whole
core `taint` population runner-side by language, track, and score tier,
exactly as the Joern and Semgrep kernels do, and each has its own report
(`reports/opentaint-<language>-kernel.json`) and retained-evidence root
(`reports/raw/opentaint-<language>-kernel/`). Both populations are post-freeze
and bind nothing.

The engine analyzes bytecode, so the runner compiles each case's fixtures in
an isolated workspace — `javac` for Java, `kotlinc` for Kotlin, a harness step
outside the timed boundary the way the Joern Rust kernel's synthesized Cargo
manifest is — and hands the analyzer a synthesized `project.yaml` in its
non-Spring `unknown` project mode with the documented all-methods entry-point
selector pinned. One committed `mode: taint` rule template per language
carries the same `__DFB_SOURCE__`/`__DFB_SINK__` placeholders the Semgrep
kernels resolve, from the same marker lines, with the resolved copy retained
per case. The analyzer's rule-load trace is retained and checked per case: the
analyzer exits zero and writes a well-formed empty SARIF even when its rule
set fails to load, so a load failure is a `runner-error` and can never read as
`not-reached`.

The pin is by release-asset digest — `analyzer/2026.08.27.17eb0fe`, jar and
models archive both SHA-256-bound — because the analyzer jar self-reports no
version anywhere; the runner witnesses both digests per run and publishes the
release tag only when they match, refusing the run otherwise. The whole
expanded core is scored in both languages: the pinned documentation declares
whole-program interprocedural JVM taint and fences nothing, so there is no
documented boundary to preregister an `unsupported` partition from, and every
engine incapacity surfaces as a measured mismatch instead.

The first runs' dominant result was a **value-kind boundary**: the engine
carried taint on reference-typed values and dropped it on numeric ones, `int`
and boxed `Integer` alike, isolated by the retained probe
(`scripts/probe-opentaint-value-kind.sh`,
`reports/raw/opentaint-value-kind-probe/`) from everything the templates
vary. Reported upstream, that boundary turned out to be the engine's
**default rule configuration**, not an engine limit —
[Amendment A11](#a11--2026-08-31-opentaints-value-kind-boundary-is-a-default-rule-configuration-and-primitive-tracking-is-enabled-in-both-kernel-templates)
records the upstream identification, the primitive-tracking probe that
verified it on the same pinned jar, and the resulting
`options: primitive-tracking: true` in both kernel templates. Under the
amended templates both populations measure the templates' semantic
dimensions across their full cores: Java scores 49/58 and Kotlin 50/58, with
the residual mismatches concentrated in a dynamic-heap-location
over-approximation family reported upstream and small
per-language false-negative sets. See
[the OpenTaint adapter notes](../adapters/opentaint/README.md) for the
eligibility evaluation, the pinned invocation, the per-template results, and
both probes.

## Infer language populations

The Infer adapter keeps C, C++, and Java as three separate populations — the
three benchmark languages the pinned v1.3.0 release actually executes,
verified in the field before adaptation. Each command selects that language's
whole core `taint` population runner-side by language, track, and score tier,
exactly as the Joern, Semgrep, and OpenTaint kernels do, and each has its own
report (`reports/infer-<language>-kernel.json`) and retained-evidence root
(`reports/raw/infer-<language>-kernel/`). All three populations are
post-freeze and bind nothing. C and C++ were the issue #82 motivation: both
were single-engine populations for benchmark-controlled interprocedural
evidence, and Infer is their second engine.

**The operable taint mode was established against the binary, not the
issue.** The historical Quandary taint checker is removed from the pinned
release — `infer help --list-issue-types` names no Quandary issue type — so
the adapter drives Pulse's taint configuration
(`--pulse-taint-config`), whose `TAINT_ERROR` issue type is enabled by
default, under `--pulse-only`.

Infer analyzes code it watches being compiled, so each case materializes its
own compile command in an isolated scratch workspace — `clang -c` /
`clang++ -c` traced by the distribution's own bundled front end for C and
C++, a traced harness `javac` for Java — and the two subprocess boundaries
the adapter observes, `infer capture` and `infer analyze`, are the retained
timing phases, the same two-phase shape the CodeQL kernels retain. One
committed Pulse taint-configuration template per language, under
`adapters/infer/config/`, carries the `__DFB_SOURCE__`/`__DFB_SINK__`
placeholders the Semgrep and OpenTaint kernels resolve, from the same fixture
marker lines; the resolved copy is retained per case, and each report's
`configuration_hash` binds all three templates. The matcher shapes are
load-bearing and pinned by test: the pinned binary's plain `procedure`
matcher is a substring match, so the C-family templates carry the anchored
`^…$` regex form and Java's the `\.…(` signature-bounded form. Two verified
silent-failure modes are guarded per run — a missing taint-configuration file
is silently ignored (exit zero, no taint question asked), and a template with
no policy would report nothing — per
[the Infer adapter notes](../adapters/infer/README.md).

The whole expanded core is scored in all three languages: the pinned
distribution declares whole-program interprocedural analysis and its taint
surface fences no construct class, so as with OpenTaint there is no
documented boundary to preregister an `unsupported` partition from, and every
engine incapacity surfaces as a measured mismatch. Reconciliation reads only
`TAINT_ERROR` results as flow claims — Pulse also reports memory-safety
issues under `--pulse-only`, and those are retained as diagnostics, never as
flow evidence — and reads the engine's own final taint step alongside the
top-level location, because Infer reports a flow through a function pointer
at the indirect callsite while its retained `codeFlows` end on the anchored
sink's own callsite. See [the Infer adapter notes](../adapters/infer/README.md)
for the eligibility evaluation, the pinned invocation, the guarded failure
modes, and the per-template results.

Beyond the kernels, Infer carries the modeling tiers for **Java alone** — the
one modeling-tier language its pinned distribution executes. Amendment A13
adds its benchmark-controlled partition row, field-evaluated by execution
before its first modeling run: categories S, P (template 3 alone), and Z are
scored — five of the twelve templates, all ten scored assertions deciding
correctly in the retained run — through the committed
`adapters/infer/config/model-java.json`, whose load-bearing gate refuses a
configuration with no `pulse-taint-policies`, an unwired sanitizer kind, or a
substring `procedure` matcher. Amendment A14 adds its tool-native row: 0 / 6,
declined on a **measured silence** — the shipped product, invoked with no
taint configuration at all, decides nothing on any of the twelve Java native
fixtures — with the run's identity witnessed from the binary as every 0 / 6
row's must be.

## FlowDroid language populations

The FlowDroid adapter keeps Java and Kotlin as two separate populations —
the two benchmark languages whose fixtures compile to the JVM bytecode the
pinned 2.15.1 release's command-line analyzer consumes, verified in the
field before adaptation. Each command selects that language's whole core
`taint` population runner-side by language, track, and score tier, exactly
as the Joern, Semgrep, OpenTaint, and Infer kernels do, and each has its own
report (`reports/flowdroid-<language>-kernel.json`) and retained-evidence
root (`reports/raw/flowdroid-<language>-kernel/`). Both populations are
post-freeze and bind nothing.

**The released CLI analyzes APKs only**, established against the binary: a
plain jar of compiled classes is refused for lack of an Android manifest,
and entry points come exclusively from the manifest's declared components.
Each case therefore materializes a minimal APK in an isolated scratch
workspace — the compiled fixtures (`javac`, `kotlinc`), a fixed harness
activity whose `onCreate` calls the fixture's own entry method (the
adapter's analogue of OpenTaint's all-methods entry-point selector), a
committed benchmark-generated binary manifest, and a D8 dex translation by
the pinned r8 jar, all pinned JVM-only pieces with no Android SDK
dependency. The materialization is harness plumbing outside the timed
boundary, like the Joern Rust kernel's synthesized Cargo manifest; the one
FlowDroid invocation is timed as `total`.

The benchmark-controlled sources and sinks use FlowDroid's native
mechanism, a sources-and-sinks definition file: one committed template
whose placeholders the runner resolves per case — the method names from the
fixture's own `DFB-SOURCE:`/`DFB-SINK:` marker lines through the shared
resolver, the exact Soot signatures witnessed from the compiled fixture
classes — with the resolved copy retained per case. The pin is the Maven
Central artifact digest plus the version the jar self-reports in its
embedded `pom.properties`, both witnessed per run (#87). Two verified
zero-exit failure modes are guarded per case: the CLI prints a failure
banner while exiting zero, and a leak-free run writes no results file at
all, so the runner requires the analyzer's own completion line before any
negative and reads the results XML's self-reported `TerminationState` —
anything but `Success` is `inconclusive`, never `not-reached`. The whole
expanded core is scored in both languages: the pinned distribution declares
whole-program context- and flow-sensitive taint analysis and fences no
construct class — reflection support is a documented opt-in flag, and the
run pins the release's defaults the way the Joern kernels pin
`maxCallDepth` — so there is no documented boundary to preregister an
`unsupported` partition from, and every engine incapacity surfaces as a
measured mismatch. See [the FlowDroid adapter
notes](../adapters/flowdroid/README.md) for the eligibility evaluation, the
pinned identities, the guarded failure modes, and the per-template results.

## Pysa language population

The Pysa adapter is one population: Python, the language the engine exists
for, selected runner-side by language, track, and score tier exactly as the
other kernels are, with its own report (`reports/pysa-python-kernel.json`)
and retained-evidence root (`reports/raw/pysa-python-kernel/`). The
population is post-freeze and binds nothing, and it completes issue #82's
intent for the language: Python is the first five-analyzer kernel — Bifrost,
CodeQL, Joern, Semgrep CE, and Pysa.

**The pin is a pair, and that is a field finding.** The pinned pyre-check
0.10.0 client no longer carries its own Python front end for this path: it
drives the separately released Pyrefly binary for module and call-graph
resolution, so the adapter pins pyre-check 0.10.0 **and** Pyrefly 1.2.0 (its
contemporaneous stable release), witnesses both self-reported versions per
run, and records both binaries' measured digests in the build identity. The
pair's one verified silent-failure mode is guarded as part of the pinned
invocation: without a `pyrefly.toml` declaring the sources as the project,
Pyrefly exports every call in the fixture as an unresolved
`EmptyPyreflyCallTarget` and the analysis finds nothing while exiting
cleanly, so the runner writes that declaration into every case workspace. A
model naming a function the fixture does not define fails loudly (exit 10)
and is a `runner-error`, and the runner additionally proves from each case's
retained evidence that both benchmark endpoints were bound — the OpenTaint
rule-load discipline — so a clean `not-reached` always carries its own
activation proof.

Endpoints are bound in Pysa's native mechanism: one committed
`taint.config` declaring the two kinds and the single rule, and one
committed `.pysa` model template whose placeholders the runner resolves per
case from the fixture's own `DFB-SOURCE:`/`DFB-SINK:` marker lines — the
same resolver every other kernel uses, plus the module name the flat
source-root materialization gives each fixture. Both committed artifacts
bind the report's `configuration_hash`, and the resolved models are
retained per case. The whole expanded 58-assertion core is scored: Pysa's
documentation declares whole-program taint analysis and fences no construct
class, so as with OpenTaint, Infer, and FlowDroid there is no documented
boundary to preregister an `unsupported` partition from, and every engine
incapacity surfaces as a measured mismatch. Reconciliation reads only the
declared rule's issues, on anchored sink callsites, from the issue's own
position and its backward-trace sink-reach positions. See [the Pysa adapter
notes](../adapters/pysa/README.md) for the eligibility evaluation, the
pinned identities, the guarded failure modes, and the per-template results.

**The adapter also holds Python's modeling and tool-native rows.** Amendment
A16 added Pysa's benchmark-controlled partition row — categories S, P, Z, O,
and E scored, ten of the twelve templates, with the category P and O
declarations made load-bearing by the `@SkipAnalysis` + `@SkipObscure` modes
after the pinned pair was measured resolving the matrix's reflective body on
its own — and Amendment A17 added its tool-native row, six of six templates
over the model suite the pinned wheel ships in `lib/pyre_check/taint/`. Both
rows are Python-scoped by the engine's own language scope, run through
`run-pysa-modeling` and `run-pysa-native`, and write
`reports/pysa-python-modeling.json` and `reports/pysa-python-native.json`
with raw evidence under the matching `reports/raw/` roots.

The checked-in Bifrost snapshot (`reports/bifrost-smoke.json`) contains 118
normalized results from Bifrost v0.10.2 build identity
`c2116609f5fc1be318c8fb76fb83763cf326bab6`: 50 `reached`, 37 `not-reached`, 30
`inconclusive`, and 1 `unsupported`. The pinned binary has SHA-256
`93b55dd20c283c278f586e8c8e6ad6bf0e9f5f08165b56096e110af0450d0873`.
The Java, Python, and JavaScript 32-assertion profiles have respectively
17/32 assertions matching expected polarity (17 of 22 decisive outcomes),
16/32 (16 of 20 decisive outcomes), and 19/32 (19 of 26 decisive outcomes);
incomplete runs remain `inconclusive`, never synthesized as `not-reached` or
counted as false negatives. The v0.10.2 outcomes match v0.10.1 case-for-case,
but do not restore the complete Java correctness observed in v0.9.5. See the
[Bifrost adapter notes](../adapters/bifrost/README.md) for raw-report
separation and the per-template mismatch breakdown.

## Amendments

Amendments are dated, state what changed and which adapters and populations
they touch, name the freezes they invalidate, and land as their own commits —
separate from any fixture, rule-template, or result change they motivate.

Their numbers continue the repository's **single** amendment sequence rather
than restarting per document: A1 is in
[the challenge tier](challenge-tier.md#amendments), A2–A5 and A9 are in
[the modeling matrix](modeling-matrix.md#amendments), A6–A8 and A10 are in
[the tool-native profile](native-profile.md#amendments), and A12 is in
[the latency tier](latency-tier.md#amendments). This document joins it here
with A11 and A30, so that an amendment identifier names exactly one amendment
wherever it is cited.

### A11 — 2026-08-31: OpenTaint's value-kind boundary is a default rule configuration, and primitive tracking is enabled in both kernel templates

**What was published.** The OpenTaint adapter (#96) measured the pinned
`analyzer/2026.08.27.17eb0fe` engine dropping taint on numeric values — `int`
and boxed `Integer` alike — while carrying it on reference types, isolated
from the templates' semantic dimensions by the retained value-kind probe
(`scripts/probe-opentaint-value-kind.sh`,
`reports/raw/opentaint-value-kind-probe/`). The adapter notes, this
document's OpenTaint sections, and both kernel contracts stated that boundary
as a property of the pinned engine, and it dominated both retained reports:
Java's core is entirely `int`-encoded, so its kernel read 0/29 on positives;
Kotlin's 15 `Int`-encoded templates repeated the same miss.

**What the upstream response measured false in that framing.** The boundary
was reported upstream as
[seqra/opentaint#388](https://github.com/seqra/opentaint/issues/388), and the
maintainers' response identified it as a **default rule configuration**, not
an engine limit: primitive tracking is disabled by default and enabled per
rule with `options: primitive-tracking: true`, exercised by the shipped
ruleset itself. The claim was verified on the same pinned jar
(digest-checked, invocation otherwise identical) by the primitive-tracking
probe (`scripts/probe-opentaint-primitive-tracking.sh`,
`reports/raw/opentaint-primitive-tracking-probe/`): with the option absent
the value-kind probe's result reproduces exactly, and with the option enabled
all four value kinds carry — including `int` and boxed `Integer` — with zero
findings on the probe's added clean and overwrite negative arms. A Kotlin
mirror of the probe (kotlinc-compiled `object` members, `Int`-typed
endpoints) behaved identically in both directions.

**What changes.**

1. Both committed kernel rule templates
   (`adapters/opentaint/rules/kernel-java.yaml`,
   `adapters/opentaint/rules/kernel-kotlin.yaml`) gain
   `options: primitive-tracking: true`, joining the templates' other two
   load-bearing spellings as a third verified against the pinned engine. The
   option puts the benchmark rule on the same footing as the shipped ruleset's
   own primitive-flow rules; leaving the default in place would keep
   publishing a rule-configuration artifact as if it were an engine
   measurement.
2. The templates' `configuration_hash` changes, which invalidates both
   retained OpenTaint kernel reports
   (`reports/opentaint-{java,kotlin}-kernel.json`); both populations are
   re-run in full under the amended templates, as their own change separate
   from this amendment. Java's 29 positives become real measurements of the
   templates' semantic dimensions rather than 29 repetitions of one
   configuration artifact, and the same holds for Kotlin's 15 `Int`-encoded
   templates.
3. The adapter notes and both kernel contracts restate the boundary as what
   it measurably is: a property of the **default** rule configuration,
   resolved for this adapter by the amended templates. The value-kind probe
   and its retained evidence are unchanged and keep their meaning — they
   measured the default configuration, and its baseline is re-reproduced in
   the primitive-tracking probe's retained evidence.

**What does not change.** The pin and both witnessed asset digests, the
invocation and its flags, the scored partition (the whole 58-assertion core
in both languages — this amendment moves no case between partitions and
remains partition-inert), the outcome semantics, and the anchored
reconciliation are all untouched. No published freeze is invalidated: neither
OpenTaint report is part of a frozen set.

### A30 — 2026-09-03: the eleven CodeQL kernel populations are re-run under the endpoint-observation probe, and a merged probe row is read as every role it carries

**What was published.** PR #137 (fixing #131) gave every CodeQL kernel a
companion endpoint-observation probe (`<Language>KernelEndpointProbe.ql`,
evaluated beside the kernel query in one `database analyze` invocation) and
folded the probe file into each population's configuration-path set, so a
zero-result SARIF is read as `not-reached` only when the probe observed both
benchmark-controlled endpoints. It changed normalization semantics and every
CodeQL kernel's `configuration_hash` without touching committed evidence —
correctly, and stated in its body — which left the eleven retained CodeQL
kernel reports (Java, JavaScript, TypeScript, Python, Kotlin, C#, Go, C, C++,
Rust, Ruby) carrying outcomes that predate the probe. PR #141 made that debt
visible: `validate-reports` now compares each report's stamped hash against
the working tree, and the eleven stems sat in `KNOWN_STALE_CONFIGURATIONS`
under issue #138, each scorecard carrying a generator-emitted staleness
caveat.

**What this amendment does.** All eleven populations are re-run in full at
the unchanged fixture revision
`sha256:9df209ed3d7723a3ee33f2b289cf2afe34a3add781bdf2a2ac445de42b8d0151`
on the pinned CodeQL CLI 2.26.4 (build
`6b1e4dee94adb20f90a671f3fc9e04be32eecf65`), through the same traced
toolchains the retained runs recorded (kotlinc-jvm 2.4.10, go1.26.0), with
no `--codeql-packs` search path: every pack resolves from the committed locks.
Each regenerated report now stamps the probe-bearing configuration hash, and
its retained SARIF carries the probe's rows as raw evidence beside the
kernel's findings. The eleven `KNOWN_STALE_CONFIGURATIONS` entries are
deleted, so the list is empty and the drift guard is armed at full strength
again.

**What the re-run measured false in the probe's reader.** The first Java and
JavaScript re-runs each turned exactly one case — the direct-propagation
positive, `recordDirect(directUntrustedInput())` and its JavaScript twin —
from `reached` to `inconclusive` under the diagnostic *"resolved 1 source
endpoint(s) and 0 sink endpoint(s)"*, although the retained SARIF shows the
kernel finding **and** both probe observations. The cause is on the
benchmark side: CodeQL merges `@kind problem` rows that share a location into
one SARIF result whose message joins the rows' texts with newlines, and in the
direct templates the sink argument *is* the source call, so both endpoints
resolve to the same expression and arrive as one result reading
`Benchmark source endpoint observed.\nBenchmark sink endpoint observed.` The
splitter (`split_codeql_endpoint_probe`) counted one role per result and so
withheld a real finding. It now counts every line of a probe result's message
(`a_merged_codeql_endpoint_probe_result_counts_every_observed_role`), and
Java and JavaScript were re-run under the corrected reader rather than
re-normalized from the retained SARIF, so their reports' timing sidecars and
environment stamps describe the run that produced them. No fixture, query,
or probe file changed, so no configuration hash moved on account of this
correction; the hash change on every population is #137's alone.

**Outcome deltas against the v0.6.1-bound reports.** Six of the eleven populations reproduce every
committed outcome under the probe — Java (58), JavaScript (58), TypeScript
(58), Kotlin (58), Go (58), and Rust (56) — so their hash change is the only
change. Five populations each move exactly one case, and it is the same case
in all five: the **infeasible-branch negative** (`if (false)` / `if False:`
guarding the source call) goes from `not-reached` to `inconclusive` for
Python, C#, C, C++, and Ruby, under the diagnostic *"resolved 0 source
endpoint(s) and 1 sink endpoint(s)"*. Each of those extractors prunes the
constant-false branch from the control-flow graph, so the source call never
exists as a data-flow node and the kernel's clean negative was vacuous in
precisely the sense the probe was preregistered to catch: the analyzer never
saw the source, and a reader cannot tell "reasoned infeasible" from "never
observed" in a zero-result SARIF. The retained SARIF shows the sink observed
and the source absent in every one of the five. Java, Kotlin, Go, Rust, and
the two ECMA extractors keep the dead branch as a node and so still observe
both endpoints; their infeasible-branch negatives stay `not-reached`. Whether
a constant-branch prune should count as a decided negative for a kernel
template whose question is infeasibility is a contract question this
amendment leaves to a later one; the outcome recorded here is what #137's
preregistered rule yields, and the five cases are excluded from the decisive
denominators as `inconclusive` rather than credited either way. No case
moves in the other direction; no `reached` outcome is lost.

**What does not change.** The pin and its witnessed build identity, the
per-case invocation (one fresh database per case, `--additional-packs` never
passed), the scored partitions and denominators (58 assertions per expanded
core, 56 for Rust's with its two language-extension cases outside the
denominator, 30 for C's classic core), the anchored reconciliation, and the
modeling matrix — which deliberately runs no probe — are all untouched. The
Bifrost half of #138 (twenty reports whose `reached` outcomes predate sink-anchor
reconciliation, invisible to a configuration-file hash) is not addressed here
and stays owed under its own amendment.

**Templates and languages touched.** Every core kernel template in all eleven
CodeQL populations; one normalization correction affecting the direct
template's positive under CodeQL only. No partition moves.

**Freezes invalidated.** v0.6.1 bound all eleven superseded reports and
their raw evidence by digest. Its manifest and evidence stay available for
audit at the `v0.6.1` tag and remain the release claim; `reports/freeze.json`
on the main line moves to a **development-scope** freeze over the same 82
reports with the eleven regenerated CodeQL reports in place of the
superseded ones, so `generate-results --check` keeps proving the checked-in
`results/` against the evidence they cite. No release or website claim is
made from the development freeze; the next release freeze binds this
evidence together with the Bifrost re-runs #138 still owes.

### A31 — 2026-09-04: the twenty Bifrost populations are re-run on v0.10.9, and every `reached` outcome is anchor-proven under sink-anchor reconciliation

**What was published.** PR #134 (fixing #127) put Bifrost's findings through
the sink-anchor gate every other adapter already had: a finding counts as
`reached` only when its primary location lands on a callsite of the case's
anchored sink function in the anchored file, and anything else is
`inconclusive`. It changed normalization semantics without touching committed
evidence — correctly, and stated in its body — so the twenty retained Bifrost
reports (thirteen kernels, the smoke slice, three modeling and three
tool-native populations) carried `reached` outcomes that were decided from a
bare finding count and never anchor-proven. PR #116, merged after the v0.6.1
freeze, changed a second rule in the same normalizer: a policy whose endpoint
selectors bind nothing is `inconclusive`, not a vacuous `not-reached`. Neither
change moves a policy file, so the configuration-hash guard from PR #141 could
not see either; issue #138 was the only record, and
[A30](#a30--2026-09-03-the-eleven-codeql-kernel-populations-are-re-run-under-the-endpoint-observation-probe-and-a-merged-probe-row-is-read-as-every-role-it-carries)
left the Bifrost half explicitly owed.

**What this amendment does.** All twenty populations — 968 results — are
re-run in full at the unchanged fixture revision
`sha256:9df209ed3d7723a3ee33f2b289cf2afe34a3add781bdf2a2ac445de42b8d0151`
on the newly pinned Bifrost v0.10.9, build
`04775a7b38c9c025714168328ddb8b793a326461`, the upstream release asset
recorded in the
[2026-09-04 pin review](#2026-09-04--v070-freeze-prep-bifrost-re-pin). Every
regenerated report is normalized by the reconciled rule, so every `reached`
it carries is one whose finding the reconciler matched against the anchored
sink's callsite. Each population's `run-environment.json` stamps the machine
and the witnessed identity, and now also the full four-line `--version`
banner (`witnessed_tool_version_banner`) whose version line is the report's
`tool_version`. The runs were not taken in a settle-gated quiet window — the
one-minute load average was between 3 and 17 across them — which the
per-case timing sidecars record and no latency claim reads; the latency
corpus stays v0.6.0-frozen.

**What the re-run measured, separated by cause.** Of 968 results, seven move
outcome. Diffing every case's diagnostics as well as its outcome against the
v0.6.1-bound report attributes them as follows.

- *Sink-anchor reconciliation (PR #134): no outcome moves.* Every one of the
  293 `reached` outcomes the superseded reports carried is reproduced as
  `reached` by the reconciler — each finding's primary location sits on a
  callsite of the anchored sink in the anchored file — and no `reached` is
  demoted to `inconclusive` for an unmatched, ambiguous, or location-less
  finding. The re-proof the twenty reports owed is therefore a confirmation:
  the pre-reconciliation `reached` set was anchor-correct throughout, and
  the generated scorecards now describe outcomes decided under the contract
  they render.
- *The v0.10.9 bump: four moves, all decided correctly.* The Go
  array-element pair goes from `inconclusive` (*"value-flow snapshot
  unsupported (`index_memory`)"*, the v0.10.8 regression filed as
  BrokkAi/bifrost-dev #2831 and closed by this release) to `reached` on the
  positive and `not-reached` on the negative; the PHP map-iteration pair goes
  from `inconclusive` (*"value-flow snapshot … is unproven"*) to the same
  correct pair. Net across the thirteen kernels: +2 `reached`, +2
  `not-reached`, −4 `inconclusive`. No case moves the other way.
- *Empty endpoint selections (PR #116): three moves, none a bump or
  reconciliation effect.* The `model-declared-source-negative` case goes from
  `not-reached` to `inconclusive` in all three modeling populations (Java,
  JavaScript, Python) under an unchanged diagnostic — the policy *"bound no
  source endpoint … so this run reports zero findings vacuously"* — which is
  exactly the vacuous negative #116 stopped crediting. The raw evidence is
  the same shape as before; only the rule that reads it changed, and it
  changed after the v0.6.1 freeze bound the reports.

**What moved beneath the outcomes.** 218 kernel results keep their outcome
but change their retained diagnostic under v0.10.9, and the shifts are
named here so no later reader mistakes them for a normalization change.
The generic *"procedure value-flow snapshot for … is unknown"* is now
reported as one of three more specific causes — *"call resolution"* (54),
*"procedure semantics"* (48), or *"access-path resolution"* (30) *"… is
unknown"*. Fifty results that v0.10.8 declined as
`capability_incomplete` — *"taint semantic binding is unavailable: no
analysis root contains both a selected source and sink"* — are now
`partial_discovery` with a named procedure, meaning the engine binds both
endpoints and says where discovery stopped. Ten recursive-carry and
nested-access-path results gain a fixed-point summary (*"2 unproven edge(s),
2 partial edge(s), and 1 open boundary row(s)"*). Four new named unsupported
signatures appear, each on a pair that was and stays `inconclusive`: C++
dispatch-table and Go anonymous-implementation (`values`), Ruby
reflective-invocation (`callable_references`), Scala callback-registration
(`deferred_execution`). And the `index_memory` signature of #2831 does not
disappear — it moves from the Go array-element pair, now decided, to the Go
map-iteration pair, previously *"unproven"* and still `inconclusive`. No
outcome moved on account of it, so it is published here rather than held
against the pin; it is a candidate for an upstream report, not a regression
this benchmark measured.

**What does not change.** Every configuration hash except two: the three
tool-native hashes move because `native_configuration_hash` binds the
witnessed binary identity, which is what the bump changes, and the
JavaScript modeling hash moves because its policy file's preregistration
comment cites the modeling matrix's Bifrost heading by anchor and that
anchor now names v0.10.9 — the policy body is unchanged. The thirteen kernel
hashes, the smoke hash, and the Java and Python modeling hashes are
byte-identical to the superseded reports', which is the guard from PR #141
confirming that no policy moved. The three tool-native populations stay
12 / 12 `unsupported` with their preregistered rationales; the modeling
partition stays S and Z scored, four categories unsupported; the scored
denominators and the anchored reconciliation contract are untouched.

**Templates and languages touched.** Every core kernel template in all
thirteen Bifrost kernel populations and the smoke slice; the S and Z modeling
categories for Java, JavaScript, and Python; the six tool-native templates
for the same three languages. No partition moves.

**Freezes invalidated.** v0.6.1 bound all twenty superseded reports and
their raw evidence by digest. Its manifest and evidence stay available for
audit at the `v0.6.1` tag and remain the release claim; `reports/freeze.json`
on the main line moves to a new **development-scope** freeze over the same
82 reports with the twenty regenerated Bifrost reports in place of the
superseded ones, the movement A30 made for CodeQL. No release or website
claim is made from the development freeze; with this amendment both halves
of #138 are re-run, and the next release freeze binds the whole set.

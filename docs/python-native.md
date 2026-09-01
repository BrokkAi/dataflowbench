# Python tool-native probe set

Wave N1's Python row of the [tool-native model profile](native-profile.md), and
the row that closes the wave and issue #16. It adds Python's twelve native
assertions over real CPython APIs, the vendored Semgrep activation snapshot its
partition needed, and runs of all four adapters against them.

It is also the only row where **Semgrep CE is scored at all**. The CodeQL run
uses the same native execution arm [JavaScript](javascript-native.md) and
[Java](java-native.md) run on — one implementation, with the language choosing
only the extractor and the pinned suite — and the Semgrep arm that lands here
reconciles through that same rule rather than a second one of its own.

Nothing in the preregistration is changed by this document. The six template
definitions, the platform-API identities, the activation contracts, and the
three-way unsupported/incomplete/runner-error distinction are fixed there and
are only *realized* here. One capability finding did move a partition, and it
was carried into the preregistration through its own amendment procedure —
[A8](native-profile.md#a8--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension),
recorded from vendored rule text **before** the first Semgrep scan of this
population.

## What these numbers are, and what they are not

**This is coverage, not accuracy.** A miss below says the vendor's shipped
model set does not cover a CPython API, or does not link two of them, or does
not credit an idiom in the query family that owns this sink. It says nothing
about whether the engine could have followed the flow had it been told — that
is the question [the benchmark-controlled matrix](python-modeling.md) asks, and
the two are never pooled, never averaged, and never presented as one number.
The two profiles do not even run on the same library resolutions: the native
CodeQL run resolves `codeql/python-all@7.2.4` out of the pinned *query* pack,
against the adapter's `7.2.3`.

**Read against 50%, not against zero.** Every template contributes one positive
and one minimally different negative, so a tool that has never heard of
`os.system` answers "no flow" on both cells and banks a free true negative per
pair. The blind baseline is 6 / 12. The per-template true-positive and
false-positive rates below carry the evidence; the raw correct count does not,
and is never published alone.

## The population

Twelve cases under `cases/taint/python/native-<short>-{positive,negative}/`,
ids `dfb-taint-python-native-<short>-<polarity>`, all `score_tier: "modeling"`,
`model_profile: "tool-native"`,
`fixture_provenance.revision: "n1-native-python"`, standard library only, and
`tool_model_references: {}` — a native run loads only models the vendor ships,
and the no-benchmark-models gate refuses a run that would load one of ours.

| # | Template | Cat. | Fixture | Platform identities | Neg. mechanism |
| --- | --- | --- | --- | --- | --- |
| 1 | `dfb-template-native-source-sink` | S | `env_command.py` | `os.environ["…"]` → `os.system` | `unrelated-value` |
| 2 | `dfb-template-native-propagator` | P | `join_command.py` | `os.path.join` | `unrelated-value` |
| 3 | `dfb-template-native-sanitizer` | Z | `quote_command.py` | `shlex.quote` | `sanitizer` |
| 4 | `dfb-template-native-summary` | O | `roundtrip_command.py` | `base64.b64encode` / `b64decode`, `str.encode` / `bytes.decode` | `unrelated-value` |
| 5 | `dfb-template-native-entrypoint` | E | `argv_command.py` | `sys.argv[1]` | `unrelated-value` |
| 6 | `dfb-template-native-persistence` | B | `store_command.py` | `os.environ[K] = v` then a read of `os.environ[K]` | `field-separation` |

Every fixture passes `python3 -m py_compile` and imports nothing outside the
standard library, which is what the
[native-binding trap](native-profile.md#the-native-binding-trap) requires: a
local `def system(cmd)` stand-in has a different identity from `os.system` and
would guarantee a miss that looked exactly like a coverage gap.

`scripts/validate-python-kernel.py` filters on `score_tier == "core"` and is
therefore blind to this population by construction — it still reports 29
templates and 58 core cases, unchanged.

### The sink is present in both cells, deliberately

Every negative keeps the `os.system` callsite, identical to its positive's.
Only the value that reaches it differs. That is not incidental: a negative that
removed the sink would let a sink-existence rule score a true negative it did
not earn, and this profile's most likely observation about any tool is a
sink-existence false positive. Where the doc's template requires it, the
*source* is present in the negative too and simply goes nowhere — the
`sys.argv` read in template 5, the environment read in templates 1 and 4 — so
the negative differs from its positive in the flow and in nothing else.

### Native anchoring binds a callsite, not a declaration

Every other population in this benchmark puts a `DFB-SINK:` marker on the
*declaration* of a benchmark-invented endpoint, and reconciliation walks that
function's callsites. A native fixture declares no endpoint at all — the sink
is inside CPython — so the marker sits on the real platform-API callsite and a
finding is bound to that line. Findings elsewhere in the fixture are retained
as diagnostics and are never flow evidence. Only genuinely unreadable evidence
makes a cell `inconclusive` — a finding whose location cannot be parsed, or one
that matches two anchors at once, which cannot arise here because every Python
native case has exactly one. A completed scan that found nothing at the anchor
is a plain `not-reached`, which on a positive cell is the false negative this
profile exists to publish; see
[outcome honesty](native-profile.md#outcome-honesty).

An anchor is still only a way to decide which finding belongs to which
assertion. It never tells an analyzer what a source or a sink is, which is the
second half of [the activation rule](native-profile.md#the-activation-rule).

## What each adapter was given

| Adapter | Activation | Scored |
| --- | --- | --- |
| CodeQL CLI 2.26.3 | `codeql/python-queries@1.8.9:codeql-suites/python-security-extended.qls`, `--threat-model=local`, no adapter query | 6 / 6 |
| Semgrep CE 1.174.0 | `--oss-only --config adapters/semgrep/native/python`, the vendored snapshot, no `taint_assume_safe_functions` | 6 / 6 (Amendment A8) |
| Bifrost v0.10.6 | built-in policy packs only | 0 / 6 |
| Joern 4.0.610 | `DefaultSemantics` only | 0 / 6 |

### The vendored Semgrep snapshot

`adapters/semgrep/native/python/` holds ninety-one rule files copied verbatim
from `semgrep/semgrep-rules` @ `40b8c63f75dc7c22c8a77482d73bfb864b146f7e`,
path `python/lang/security/` including its `audit/` subtree, with the upstream
`LICENSE` beside them and a `provenance.json` recording `kind: derived`, the
repository, the commit, the upstream paths, the licence, the retrieval date,
and a SHA-256 per file. Nothing is modified: a vendored rule *is* the product
under test, and editing one would be editing the vendor's model. The runner
refuses to start if the provenance file is missing, and the report's
`configuration_hash` binds its bytes — which, through the per-file digests,
binds the rules.

Registry configurations (`--config p/…`) are network-fetched and unpinnable at
run time; two runs a week apart would be two different rulesets under one name.
Vendoring is what makes the Semgrep column a benchmark rather than a date.

### Bifrost and Joern were never asked about a fixture

Both enter at 0 / 6, so all twelve of each one's cells are decided from the
template identity before any analysis starts, and each writes a retained
`unsupported` decision naming the tool identity, the activation identity, and
the preregistered rationale verbatim.

This row was originally published with a stronger claim — that the binary was
never touched at all, verified by running
`run-joern-native --language python --joern /nonexistent/joern` and getting
byte-identical evidence — and with version fields carrying the pinned identity
the partition was decided against rather than an observed banner, on the
reasoning that a 0 / 6 run has nothing to observe. The second half of that was
wrong, and is corrected in
[the run-level identity is witnessed](native-profile.md#the-run-level-identity-is-witnessed-including-at-0--6):
a 0 / 6 run has nothing to observe *about a fixture*, but it still has to say
which binary it was pinned to, and it now reads that binary's version banner
once to find out. The cell-level claim is unchanged and unconditional: no
declined cell is handed to the analyzer, and the retained decisions are
byte-identical whatever the binary reports. The nonexistent-path check no
longer holds, by design — a run that cannot witness its own pin fails instead
of asserting one.

These are capability coverage, never negatives. They never become a clean
negative and never reduce anyone's denominator, and the gap between Joern's
0 / 6 here and its 4 / 6 *categories* on the benchmark-controlled matrix with
the same engine is exactly what this profile exists to make legible: it is a
statement about the OSS distribution's product packaging, not about its engine.

## Results

Reports are `reports/<tool>-python-native.json` with raw evidence under
`reports/raw/<tool>-python-native/`. No freeze manifest contains any of them:
the v0.4.0 claim is `benchmark-controlled` at the `calibration`, `core`, and
`language-extension` tiers, and these are new paths outside it.

| Adapter | Scored | TP rate | FP rate | Correct | vs. blind 6 / 12 |
| --- | --- | --- | --- | --- | --- |
| CodeQL CLI 2.26.3 | 12 | 6 / 6 (100%) | 2 / 6 (33.3%) | 10 / 12 (83.3%) | +4 |
| Semgrep CE 1.174.0 | 12 | 6 / 6 (100%) | 4 / 6 (66.7%) | 8 / 12 (66.7%) | +2 |
| Bifrost v0.10.6 | 0 | — | — | — | no denominator |
| Joern 4.0.610 | 0 | — | — | — | no denominator |

Both activated tools found **every positive**. Neither missed a flow. Every
error either made is a false positive on a negative, which is a different
product fact from a coverage gap and is why the two rates are published
together.

### Per template

| # | Cat. | Template | CodeQL pos / neg | Semgrep pos / neg |
| --- | --- | --- | --- | --- |
| 1 | S | `native-source-sink` | TP / **TN** | TP / **TN** |
| 2 | P | `native-propagator` | TP / **TN** | TP / *FP* |
| 3 | Z | `native-sanitizer` | TP / *FP* | TP / *FP* |
| 4 | O | `native-summary` | TP / **TN** | TP / *FP* |
| 5 | E | `native-entrypoint` | TP / **TN** | TP / **TN** |
| 6 | B | `native-persistence` | TP / *FP* | TP / *FP* |

Read beside [the benchmark-controlled Python card](python-modeling.md), category
for category — and never added to it.

### CodeQL — 10 / 12

One rule decided every cell: `py/command-line-injection`, from the shipped
`python-security-extended` suite. No other query in the suite fired on any
fixture, which is worth stating because it means the whole column is one
query family's behaviour.

The suite's shipped model set covers all six CPython identities the templates
name, and covers them *through* the platform: the base64 round trip (template
4) and the `os.path.join` hop (template 2) both carry taint to the sink, and
both negatives are correctly silent, so those are genuine flow decisions rather
than sink-existence noise. `--threat-model=local` is load-bearing for templates
1, 5 and 6; without it the default `remote`-only threat model would have
decided them all for a reason that has nothing to do with coverage.

The two false positives are the two hazards the preregistration named in
advance, and both are now measured rather than predicted:

**Z — `shlex.quote` is not credited by the family that owns this sink.** The
preregistration states that `shlex.quote` is a barrier only for
`py/shell-command-constructed-from-input`
(`UnsafeShellCommandConstructionCustomizations.qll`) and a plain taint summary
in `Stdlib.model.yml`. The sanitizer negative routes an environment read
through `shlex.quote` into `os.system`, and `py/command-line-injection` reports
it anyway; `py/shell-command-constructed-from-input` — the one family that
would have credited the barrier — never fires, because its sink is a shell
command *constructed* for `subprocess`, not `os.system`. So the doc's
preregistered expectation holds in the sharper form: the credit exists, it is
scoped to exactly one query family, and that family is not the one that owns
this sink. That is a publishable fact about where a sanitizer's credit is
scoped, not a defect in the fixture.

**B — the store read is a source, so the key never gets looked at.** The
persistence negative writes under `DFB_NATIVE_STORED` and reads under
`DFB_NATIVE_OTHER`. `py/command-line-injection` reports it, because
`os.environ` is itself a shipped `environment` source: the read is treated as a
fresh source rather than as a keyed read of a store, and the distinct key is
exactly what is not being looked at. The shipped Java model's own comment says
the get/set key matching "needs to be modeled by regular CodeQL … to reduce
FPs"; the Python side reproduces the behaviour that comment anticipates. The
positive's true positive therefore tells us nothing about whether the
write/read link is modeled — it would have fired on the read alone — which is
why this template's two cells are only meaningful as a pair.

Configuration hash
`73de6c6787622ca988d0b4f6be9a972ece7e19b42c70964aa48960133d19e15d`; build
identity `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`.

### Semgrep CE — 8 / 12, and the sink-existence rule doing exactly what was predicted

Two vendored rules decided every cell, and which of the two fired is the whole
story:

- `audit/dangerous-system-call-tainted-env-args` — `mode: taint`, sources
  `os.environ` / `os.getenv` / `sys.argv`, sinks `os.system` and `os.popen*`.
  This is the rule Amendment A8 promoted the column on.
- `audit/dangerous-system-call-audit` — a **pattern** rule, bare
  `os.system(...)` with a `pattern-not: os.$W("...", ...)` exclusion and no
  taint anywhere.

The taint rule fired on all six positives and on two negatives (Z and B). The
audit rule fired on all six positives and on **four** negatives, and it is the
sole finding on two of them.

Under [the sink-existence rule](native-profile.md#sink-existence-only-findings-and-how-they-score)
this scores exactly as written: polarity is about the flow, so a finding that
fires on sink existence alone is a true positive on the positive cell and a
false positive on the negative cell. Cell by cell:

- **P and O are pure sink-existence false positives.** The propagator and
  summary negatives pass a *clean* value to `os.system`, and the taint rule
  correctly stays silent on both. The audit rule flags them anyway, because
  the argument is a variable rather than a string literal and the literal
  exclusion is all the rule has. Nothing about taint entered into either
  finding.
- **S and E earn their true negatives.** Both negatives pass the literal `"id"`
  through a local, and CE's `symbolic_propagation` resolves it back to a
  literal, so the audit rule's own exclusion catches it. That is the exclusion
  working; it is also the reason it fails on P and O, where the value is a real
  computation.
- **Z and B are taint-rule false positives**, the same two the preregistration
  named for CodeQL and for the same reasons. The vendored rule declares no
  `pattern-sanitizers` at all — `shlex.quote` appears in the
  `dangerous-subprocess-use` and `dangerous-asyncio-*` families and in no rule
  that owns `os.system` — and its `os.environ` source pattern matches the
  store read whatever key is subscripted.

`taint_assume_safe_functions` is deliberately **not** set here, unlike in the
benchmark-controlled matrix, and that difference is visible in the result:
CE's permissive default is what carried the value through `os.path.join` and
through the base64 round trip on the P and O positives. Setting it would have
been editing the vendor's configuration, which the activation rule forbids —
here the default *is* the product.

Configuration hash
`e6b4975cdf103c322e96d48de82f2098dfecc1a9fcd85151ff471190f825b335`; build
identity `semgrep-oss:1.174.0`.

### Bifrost and Joern — no denominator

Twelve `unsupported` outcomes each, decided before invocation, with the
preregistered rationale retained verbatim in every raw evidence file:
`adapters/bifrost/README.md`'s own statements about sanitizer lowering and
external activation for Bifrost, and the decompiled `DefaultSemantics` — flow
constraints only, no source catalog, no sink catalog — for Joern. Neither has a
tool-native Python denominator, which is different from having a zero.

## Reproducing

```bash
cargo run -- run-codeql-native  --language python --codeql /opt/homebrew/bin/codeql
cargo run -- run-semgrep-native --language python --semgrep /opt/homebrew/bin/semgrep
cargo run -- run-bifrost-native --language python --bifrost bifrost
cargo run -- run-joern-native   --language python --joern joern
```

The CodeQL run downloads the pinned query pack on first use. The Semgrep run
needs the vendored snapshot in the tree; a missing `provenance.json` is a hard
error that fails the build, never an `unsupported` and never a result.

## Invariants this wave upheld

- No aggregate anywhere combines these numbers with the Python kernel's or with
  [the Python modeling matrix's](python-modeling.md).
- No case here entered a benchmark-controlled selection, and no
  benchmark-controlled case entered a native run; the corpus-wide
  profile-disjointness check asserts it.
- No native run supplied a benchmark-authored model of any kind.
- No fixture was adjusted and no vendored rule was edited to make a shipped
  model fire. A shipped model that does not cover a platform API is a product
  fact, and it is published as one.
- The partition was fixed before every run, and the one promotion is a dated
  amendment made from rule text before the scan it affects.

## Pysa joins the probe set (Amendment A16)

Python's native row gained a fifth adapter after wave N1 closed:
[Amendment A16](native-profile.md#a16--2026-09-01-pysa-joins-the-tool-native-profile-with-a-live-activation-row)
added Pysa over the model suite the pinned pyre-check wheel ships in
`lib/pyre_check/taint/` — activated by pointing `taint_models_path` at it
with `--no-verify`, both facts established by probe
(`reports/raw/amendment-a16-pysa-native/`) — with all six templates scored
and the expectation preregistered: a near-blind-baseline score, because the
shipped source catalog is framework-shaped and models neither a bare
`os.environ` read nor a `sys.argv` subscript.

**The scored run — `reports/pysa-python-native.json` — lands exactly on that
expectation: 6 / 12, the blind baseline.** All twelve cells are
`not-reached`: every positive is a coverage miss by an activated suite —
the retained evidence carries the shipped `os.system` sink model in every
cell, so the suite demonstrably loaded and simply had no source to start
from — and every negative is the free true negative the
[blind-baseline reading](scoring.md#balanced-pairs-and-the-blind-baseline)
prices in. Read beside [the modeling row](python-modeling.md), the pair of
rows says something precise: handed equivalent models, this engine activates
five of six categories flawlessly; as shipped, its suite covers none of these
platform reads. That is the product-versus-engine distinction the two
profiles exist to keep separate, and Pysa is its sharpest example yet —
sharper than Joern's, whose native zero is a packaging fact rather than a
measured sweep of misses. Notably, not one shipped rule fired on sink
existence alone: unlike the vendored Semgrep audit rules, the suite's
taint-mode rules stay silent on a clean flow into `os.system`, so the six
true negatives are earned by silence rather than luck — but with every
positive also silent, silence is all this measurement got to see.

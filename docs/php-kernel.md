# PHP propagation kernel

Issue #40 ports the sixteen scored Java propagation templates to PHP, as
classified in the [applicability matrix](applicability-matrix.md). The PHP cases
keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to PHP syntax. Every
scored PHP template has exactly one `positive` and one `negative` `core` case,
so the classic PHP core denominator is 16 templates and 32 assertions, exactly
as the matrix fixes it.

**PHP's core has since expanded.** The
[challenge-tier preregistration](challenge-tier.md) classifies all thirteen of
its templates as directly applicable to PHP, and this contract's
[challenge-tier expansion](#challenge-tier-expansion-13-templates-58-assertions)
section records the fixtures, the adaptation notes, and the observed
per-stratum results. **PHP's v0.4.0 expanded core denominator is 29 templates
and 58 assertions.** The v0.3.0 sixteen-template core and the expanded core are
different populations of the same name and are never compared number to number;
the classic 32 and the challenge 26 are therefore reported apart from each
other throughout.

## The classic sixteen

| Stratum | Template ID | PHP adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | A local `string` is either preserved or reassigned to a constant before the sink. |
| Local | `dfb-template-local-multi-step-chain` | Three local variables carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | PHP integer arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One `relay` function is called with a tainted and a clean value; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | `chooseFirst` returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop function return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two nested function returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Two `Holder` class instances with the same typed property stand in for the distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One `Holder` instance has separate `$tainted` and `$clean` properties. |
| Heap/separation | `dfb-template-alias-propagation-separation` | `$alias = $original;` copies the object *handle*, so the alias observes the store; a second `new Holder()` stays a distinct object. |
| Heap/separation | `dfb-template-array-element-separation` | **Language-adapted.** A PHP ordered-map array with distinct string keys stands in for the Java array's distinct constant indices. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the tainted path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A three-iteration `for` loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | A `FlowException extends \Exception` carries the value in a typed property across `throw`/`catch`. |

Exactly one cell is language-adapted, and it is the one cell the matrix
classifies as adapted. This contract records no deviation from the matrix.

## The three cells the issue calls out

**Array-element separation is adapted; nothing else in the heap stratum is.**
PHP has no fixed-length array type: `array` is a single ordered map keyed by
integers *or* strings. The pair therefore separates two elements by distinct
string keys rather than by distinct constant indices:

```php
$values = ["tainted" => "clean", "clean" => "clean"];
$values["tainted"] = dfb_source(); // DFB-WITNESS: array-element-store
$values["clean"] = "clean";
dfb_sink($values["tainted"]);      // the negative reads $values["clean"]
```

The semantic question is unchanged: can the analyzer keep two elements of one
aggregate apart? Only the spelling of "which element" moves from an index to a
key.

**Objects are ordinary classes, and alias propagation is *directly*
applicable.** PHP variables hold object *handles*, so plain assignment
(`$alias = $original;`) makes two names observe one object, exactly as Java
reference assignment does. No pointer, reference (`&`), or wrapper type is
needed, which is why the matrix classifies this cell `direct` for PHP where it
is `adapted` for Go, C, C++, and Rust. The fixtures use typed public properties
so the construct is idiomatic modern PHP rather than dynamic property creation.

**Exception-catch is directly applicable through an `\Exception` subclass.**

```php
class FlowException extends \Exception
{
    public string $value = "clean";
}
```

The positive stores the controlled value into `$flow->value` before `throw`; the
negative stores a constant and discards the controlled value. The pair differs
only in the value that crosses the transfer, so it asks the same source-to-sink
question the Java `throw`/`catch` template asks. PHP needs none of the
substitutions Go (`panic`/`recover`) or Ruby (`raise`/`rescue` naming) required.

## Fixtures

All PHP fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names, mirroring the PHP direct-flow fixture already in the breadth
slice. Each fixture is a single `.php` file that opens with `<?php`, declares
parameter and return types, uses `//` line comments and four-space indentation,
and requires no autoloader, `include`, or Composer manifest. Every one of the 58
fixtures — the 32 classic and the 26 challenge ones — passes `php -l` under
**PHP 8.5.9 (cli)**, the Homebrew build installed for this tranche. Adapters may
lower the endpoints through their own models, but the case metadata stays
analyzer-neutral and reports retain only observed evidence.

## Case population and the frozen direct pair

The PHP population is the 58 `taint`/`core` cases under `cases/taint/php/`:
thirty authored for the classic kernel with `fixture_provenance.revision`
`m2-php-kernel`, twenty-six authored for the challenge tier with revision
`m3-challenge-php`, and the two frozen direct-propagation cases. The
direct-propagation pair (`dfb-taint-php-direct-positive`
and `dfb-taint-php-direct-negative`) predates it: it is the PHP member of the
13-language direct-flow breadth slice and is frozen byte-for-byte in the
published v0.2.0 and v0.3.0 manifests. Its `case.json` therefore keeps
`fixture_provenance.revision` `m1a-direct-core` and keeps the breadth policy
reference `adapters/bifrost/policies/core-direct.rqlp`.

Editing those two files would invalidate the published evidence, so the runner
accommodates them instead: the Bifrost PHP selector accepts either
`core-php-kernel.rqlp` or the breadth `core-direct.rqlp` policy for a PHP core
case, and evaluates each case through the policy it declares. The same case is a
member of two populations, but its results are never pooled: the breadth result
lives in `reports/bifrost-smoke.json` and the kernel result in
`reports/bifrost-php-kernel.json`.

## Challenge-tier expansion: +13 templates, 58 assertions

[The challenge-tier preregistration](challenge-tier.md) fixes thirteen further
templates before any of them was authored or run, and classifies **all thirteen
as directly applicable to PHP** — the only language besides JavaScript,
TypeScript, and Ruby with no adapted cell in the tier. PHP is wave 4. Its
`CHALLENGE_ROLLOUT` row is now flipped, so **PHP's v0.4.0 expanded core
denominator is 29 templates and 58 assertions**, exactly the figure the
preregistration's denominator table fixes.

Twenty-six fixtures were authored, one `positive` and one minimally different
`negative` per template, under `cases/taint/php/<short>-{positive,negative}/`
with ids `dfb-taint-php-<short>-<polarity>`. All are `score_tier: "core"`,
`model_profile: benchmark-controlled`, provenance `authored`/`DataFlowBench`,
revision `m3-challenge-php`, licence MIT, and each is a single stdlib-only
`.php` file with no `include`, no autoloader, and no Composer manifest. All 26
pass `php -l` under PHP 8.5.9 (cli).

**Every one of the 26 fixtures was additionally *executed*** under that
interpreter with `dfb_sink` replaced by an echoing stub, and each printed
exactly the value its polarity claims — `tainted` from all thirteen positives
and `clean` from all thirteen negatives. PHP's dynamic member and variable-call
constructs are the ones most easily written to *look* right while carrying a
different value, so the ground truth of this tier is established by execution
rather than by reading.

### Adaptation notes

No cell is language-adapted. Each is authored with the construct the
preregistration's PHP paragraph names.

| Stratum | Template | PHP construct |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | **Variable method call.** `$name` holds a string constant and the call site is `$target->$name(dfb_source())` — the callee is never a syntactic name at the call site. The positive's constant is `"leak"`, the negative's `"drop"`, a sibling method on the same `Target` receiver that discards its argument and sinks a constant. `call_user_func` was available and deliberately not used: the preregistration's PHP cell names `$o->$name($v)`, and a benchmark function call would have introduced a stdlib model as an intermediary. |
| A | `dfb-template-chal-computed-property` | **Variable property access**, `$holder->{$key}`, written and read through the same local key variable. The negative uses two provably distinct constant keys, `"alpha"` for the write and `"beta"` for the read, against a `Holder` with two typed `string` properties. PHP needs no reflection adaptation here, unlike Java, C#, Go, C++, and Rust. |
| A | `dfb-template-chal-dispatch-table` | A PHP array literal of two **closures** keyed `"leak"` and `"drop"`, selected by a local key variable and invoked as `$table[$key](dfb_source())`. Stdlib only — an ordered-map array and two anonymous functions, no container library. |
| B | `dfb-template-chal-closure-capture` | A `use`-clause closure: `makeReporter()` binds the tainted local and returns `function () use ($captured) { dfb_sink($captured); }`, invoked by the caller after the creating frame has returned. The negative captures a clean local instead; the tainted local is still created and bound, so the separation is `unrelated-value` and not a missing source. |
| B | `dfb-template-chal-function-field` | A `Holder` with a typed `?\Closure $fn` property. Two instances, one holding a sinking closure and one an argument-dropping closure; a separate `dispatch(Holder $holder, string $value)` reads the field and calls it as `($holder->fn)($value)` — the parenthesis is required, since `$holder->fn($value)` would be a method call. The negative passes the second holder: `object-separation`. |
| B | `dfb-template-chal-callback-registration` | A `Registry` with an `array $hooks`, a `register(\Closure $hook)`, and a `fire(string $value)` driver that `foreach`es and invokes. Zero frameworks: twenty lines of core PHP. The negative's registered closure ignores its parameter and sinks a constant. |
| B | `dfb-template-chal-anonymous-implementation` | **Genuine anonymous classes**, which PHP has and most statically-flavored languages in this matrix do not: `new class implements Handler { public function handle(string $value): void { ... } }`. Two of them, one forwarding and one dropping, each assigned to a local and invoked through it. Neither captures anything, which keeps the cell distinct from the closure-capture one; the interface `Handler` is declared locally in the same file. |
| C | `dfb-template-chal-map-iteration` | A string-keyed PHP array, retrieved by `foreach ($records as $key => $value)` with the sink in the loop body — never by a keyed read. The negative iterates a second, disjoint array. |
| C | `dfb-template-chal-nested-access-path` | Three classes giving `$outer->middle->inner->value`, written and read at the identical depth-3 path; `Middle` and `Outer` construct their child in `__construct`. The negative reads the sibling `$outer->middle->inner->other`. |
| C | `dfb-template-chal-element-object` | `$items = [new Item(), new Item()];` with the tainted value in `$items[0]->value`. The negative reads `$items[1]->value`, so deciding it needs element separation *and* field separation together. The elements are separated by distinct constant integer indices, so the mechanism is `field-separation`, per the preregistration's default and the precedent of the classic `dfb-template-array-element-separation`. |
| D | `dfb-template-chal-deep-relay-chain` | Six same-file functions `relay1` … `relay6`, no branching and no state, with the sink at hop 6. The negative feeds the identical chain a clean constant and discards the source's value into an unused local, so the source is live in both cells. |
| D | `dfb-template-chal-recursive-carry` | `carry(string $value, int $depth)` returning `$value` at `$depth === 0` and `carry($value, $depth - 1)` otherwise, invoked with `5`. The negative's base case returns a clean constant — `overwrite-kill`. |
| D | `dfb-template-chal-context-pair-depth2` | The same `wrapper`/`helper` pair reached through two distinct two-deep paths, `outerTainted` and `outerClean`, per **Amendment A1**: `helper` returns its argument, `wrapper` returns `helper`'s result, each outer context returns that, and the caller sinks the tainted result in the positive and the clean result in the negative. Both outer contexts and both two-deep paths are live in both cells, which is what makes the negative a context question rather than a dead-code one. |

### Feature tags and declared capabilities

Taken verbatim from the preregistration, which fixes them per template:
`reflective-dispatch` (1), `higher-order` (3–7), `computed-access` (2, 8),
`ambiguous-dispatch` (3, 7), `heap-access-path` (9, 10),
`interprocedural-deep` (11, 13), and `recursive` (12); with
`expected_analysis_capability.kind` values `reflective-dispatch-taint`,
`computed-member-access-taint`, `indirect-callee-resolution-taint`,
`closure-capture-taint`, `heap-stored-callee-taint`,
`inverted-control-callback-taint`, `container-iteration-taint`,
`deep-access-path-sensitive-taint`, `element-scoped-field-sensitive-taint`,
`deep-interprocedural-relay-taint`, `recursive-carry-taint`, and
`two-level-context-sensitive-taint`.

No challenge case is tagged `intraprocedural`. That is a property of the
templates, not a choice about Semgrep, and it is what puts the whole tier in
Semgrep CE's `unsupported` partition below.

`tool_model_references` carries a `bifrost` policy entry only — the language
kernel policy `adapters/bifrost/policies/core-php-kernel.rqlp` — because PHP has
no CodeQL pack to reference. That mirrors PHP's classic non-frozen cases
exactly.

## Analyzer coverage

**CodeQL CLI 2.26.3 — the pinned version — has no PHP support at all.** There is
no PHP extractor, no `codeql/php-*` pack, and therefore no PHP database that
could be queried. This is recorded here as *analyzer coverage*, exactly as
[the applicability matrix](applicability-matrix.md) requires. It is **never**
recorded as results: there is no `adapters/codeql/php/` pack, no
`run-codeql-php-kernel` command, no `codeql` entry in any PHP case's
`tool_model_references`, and no PHP row in any CodeQL report. An absent analyzer
produces no outcomes — not `not-reached`, not `unsupported`, not anything.

PHP's analyzers are therefore **Bifrost**, **Joern** (#14), and the bounded
**Semgrep CE** adapter. The Joern adapter landed in #50 with the Java,
JavaScript, and Python kernels; PHP is the fourth language on it, and the one
for which Joern carries the most weight, since no CodeQL opinion exists to
compare against. Semgrep CE scores only its documented intraprocedural
partition, so it is coverage of a narrow slice rather than a third full
opinion.

### Adapter coverage of the expanded population

All three adapters ran here over the whole 58-assertion population. **No PHP
report is freeze-bound**: `reports/freeze.json` (v0.3.0) digest-binds nineteen
reports — the Bifrost smoke report, eight Bifrost kernel reports, and all ten
CodeQL kernel reports — and none of them is a PHP report. The three PHP reports
below are therefore whole-population replacements, not appends, and nothing
frozen was overwritten.

| Adapter | Report | Status for the expanded core |
| --- | --- | --- |
| Bifrost `run-bifrost-php-kernel` | `reports/bifrost-php-kernel.json` | **Ran** — whole-population replacement; post-freeze report, not freeze-bound |
| Joern `run-joern-php-kernel` | `reports/joern-php-kernel.json` | **Ran** — whole-population replacement |
| Semgrep CE `run-semgrep-php-kernel` | `reports/semgrep-php-kernel.json` | **Ran** — whole-population replacement |
| CodeQL | — | **No adapter exists**: the pinned CLI has no PHP extractor |
| Bifrost smoke | `reports/bifrost-smoke.json` | **Frozen and unchanged** — pinned at 118 classic cases by contract |

Nothing is deferred for PHP. The re-run-at-freeze deferral that the Java,
JavaScript, Python, TypeScript, Kotlin, C#, Go, C++, and C waves had to record
for their freeze-bound Bifrost or CodeQL slices does not apply here, because
PHP's Bifrost report was produced after the v0.3.0 freeze and PHP has no CodeQL
pack to defer. The absence of CodeQL evidence for PHP is an absence of an
extractor, recorded above as analyzer coverage, and it is not a deferral.

The Bifrost smoke report is frozen at 118 cases and is not a PHP kernel slice
that grows: `smoke_population_case` excludes the challenge tier outright, so the
smoke population is unchanged by this expansion, and the frozen PHP direct pair
keeps reporting into it through the breadth policy it declares.

## Bifrost selection and reproduction

The Bifrost PHP slice uses the language-qualified policy
`adapters/bifrost/policies/core-php-kernel.rqlp`, whose source and sink
selectors are `(language php (call :callee (name "dfb_source")))` and
`(language php (call :callee (name "dfb_sink")))`, with argument index 0 as the
dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-php-kernel --bifrost /path/to/bifrost
```

The command selects only the 58 PHP core assertions, materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-php-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-php-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

## Joern selection and reproduction

```bash
cargo run -- run-joern-php-kernel --joern <joern-cli>/joern
```

The command selects the same 58 assertions runner-side (`language == "php"`,
`track == "taint"`, `score_tier == "core"`) and drives the single shared kernel
script `adapters/joern/queries/kernel.sc` with `language=PHP`, which selects the
pinned distribution's `php2cpg` frontend. One cold CPG is built per case inside
a per-case scratch root, and the retained evidence document is written to
`reports/raw/joern-php-kernel/<case id>.json`.

`php2cpg` shells out to its bundled PHP-Parser
(`<joern-cli>/frontends/php2cpg/bin/php-parser/php-parser-4.15.10.phar`),
which is itself a PHP program, so **a host `php` interpreter must be on `PATH`**
for this kernel to run at all. The observed interpreter was PHP 8.5.9 (cli),
Homebrew. Without it the frontend fails and the script's own `catch` retains a
`runner-error` document — an unavailable frontend can never look like a negative.

The endpoint identifiers are read out of each fixture's own `DFB-SOURCE:` and
`DFB-SINK:` marker lines, never assumed, exactly as for the other five Joern
kernels.

## Semgrep CE selection and reproduction

```bash
cargo run -- run-semgrep-php-kernel --semgrep /path/to/semgrep
```

The command selects the same 58 assertions and partitions them from the case
metadata *before* Semgrep is invoked: only the seven `intraprocedural`
templates — 14 assertions — are scored, and everything else is `unsupported` by
declared capability. All 26 challenge assertions fall in that `unsupported`
partition by the preregistered `CHALLENGE_SEMGREP_PARTITION` table, so the
scored subset is unchanged at 14 by this expansion. See
[the Semgrep adapter evidence](../adapters/semgrep/README.md) for the pinned
version, the documented-scope citations, and the partition rule.

## Anchor evidence and result semantics

Analyzer output is evidence, not ground truth by itself. The runner reconciles
each retained flow's element locations with the case's `DFB-SINK:` anchor. That
marker identifies the anchored sink function *declaration*; the flow
legitimately lands on the *callsite*, so matching does not require the marker's
own line.

PHP needs its own arm of the shared reconciler (`AnchorDialect::Php`) for two
surface rules derived from these fixtures:

- **Declaration.** PHP declares a function name immediately before its
  parameter list, the same shape C#, Go, Java, and Python use, so the declared
  name is the identifier preceding the `(`.
- **Callsite.** PHP reaches an instance member through `->` and a static member
  or class constant through `::`, so a name preceded by `>` or `:` is a member
  call, not a call of the free benchmark function. Its `.` is string
  concatenation, **not** a member operator, so — uniquely among the dialects
  here — a call preceded by `.` *is* a genuine callsite and must not be
  excluded. PHP also opens a line comment with either `//` or `#`, so both are
  stripped before a line is inspected.

A successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing, ambiguous, or unmappable location
evidence is `inconclusive`, an explicitly unsupported capability is
`unsupported`, and a frontend, engine, policy, or runner failure is
`runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 16 balanced assertions.


## Observed results

All three retained snapshots cover all **58** PHP core assertions, at fixture
revision
`sha256:f74647fe824ca9f6900c48aa9d403f0e9f59230e4193e0b02bd65e29a9e4e660`.
`fixture_revision` digests the whole case corpus, so landing 26 PHP cases moved
it for every run after this wave; the other languages' reports still carry the
revision current when they ran and remain valid evidence for the populations
they were run against. They are re-run together at the v0.4.0 freeze prep.

The three reports are separate populations and are not pooled with each other
or with any other language. Within each, the classic 32 and the challenge 26
are reported apart, and the challenge strata are the preregistration's:
**A** dynamic dispatch and reflection (templates 1–3), **B** higher-order flow
(4–7), **C** containers and deep access paths (8–10), **D** context and depth
stress (11–13).

Read stratum A and template 7 as approximation character, not as a ranking —
the preregistration says so in advance, and nothing observed here changes that.
`inconclusive`, `unsupported`, and `runner-error` are capability or execution
coverage and are never converted into negatives.

### Bifrost v0.10.5 — `reports/bifrost-php-kernel.json`

Build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`. Configuration hash
`eff9c5d510d5ee7670b55350b72f5d15a87b536fe961870910a44eb75c8b5d59`, unchanged
from the previous PHP snapshot: no policy was touched for this expansion, and
the hash still covers both `core-php-kernel.rqlp` and the breadth
`core-direct.rqlp`, because the frozen direct pair is evaluated through the
policy it declares.

58 results: 12 `reached`, 10 `not-reached`, 36 `inconclusive`, with zero
`unsupported` and zero `runner-error`.

| Stratum | n | Correct | TP | TN | FP | FN | Non-decisive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 17/32 | 9 | 8 | 1 | 0 | 14 `inconclusive` |
| A — dispatch/reflection | 6 | 0 | 0 | 0 | 0 | 0 | 6 `inconclusive` |
| B — higher-order | 8 | 0 | 0 | 0 | 0 | 0 | 8 `inconclusive` |
| C — containers/paths | 6 | 0 | 0 | 0 | 0 | 0 | 6 `inconclusive` |
| D — context/depth | 6 | **4/6** | 2 | 2 | 0 | 0 | 2 `inconclusive` |
| Challenge total | 26 | 4 | 2 | 2 | 0 | 0 | 22 |
| **Expanded core** | **58** | **21/58** | 11 | 10 | 1 | 0 | 36 |

**The classic 32 reproduce the previously published PHP snapshot exactly** —
10 `reached`, 8 `not-reached`, 14 `inconclusive`, 17 of 18 decisive outcomes
correct, and the same single decisive mismatch,
`dfb-taint-php-infeasible-branch-negative`, where Bifrost reports a flow through
an `if (false) { ... }` body. That is the control this run needed: the
expansion did not disturb the population it was added to.

On the challenge tier the engine produces **no false positives and no false
negatives**. Every cell it does not decide, it declines, and it says why in
retained diagnostics:

- **12 `capability_incomplete`** — "taint semantic binding is unavailable: no
  analysis root contains both a selected source and sink": both cells of
  `reflective-invocation`, `dispatch-table`, `closure-capture`,
  `function-field`, `callback-registration`, and `anonymous-implementation`.
  Where the callee is named by a run-time string, selected from an array of
  closures, captured by a `use` clause, stored in a `?\Closure` property,
  fetched from a hook list, or supplied by an anonymous class, the engine
  cannot bind a source and a sink into one analysis root at all. That is the
  whole of stratum B plus two thirds of stratum A.
- **8 `capability_incomplete`** — "taint discovery is incomplete: procedure
  value-flow snapshot … is unsupported (assignments)": both cells of
  `computed-property`, `map-iteration`, `element-object`, and
  `nested-access-path`. This is the same "unsupported (assignments)" boundary
  the classic heap/separation stratum already hits, now reached by the
  variable-property write, the array store, the array of objects, and — for the
  nested path, uniquely — the `Middle.__construct` procedure rather than `run`.
- **2 `partial_discovery`** — "procedure value-flow snapshot for … `carry` is
  unknown": the `recursive-carry` pair. The positive additionally carries a
  "Controlled input reaches the benchmark sink" finding, which under an
  incomplete analysis is not a decisive outcome and is not scored as one.

The four decided challenge assertions are all in stratum D and all correct:
`deep-relay-chain` both cells and `context-pair-depth2` both cells. Bifrost
follows the six-hop relay and separates the two two-deep contexts — the two
cells the preregistration calibrated past a k-bounded engine — and declines
recursion.

All 58 raw Bifrost JSON reports are retained under
`reports/raw/bifrost-php-kernel/`. Per-case wall clock ranged from 45 ms to
207 ms (5.0 s for the population), far inside the 60-second `execution_budget`.

### Joern 4.0.610 — `reports/joern-php-kernel.json`

Build identity `joern-cli:4.0.610`, `php2cpg` frontend over PHP 8.5.9 (cli).
Configuration hash
`ab10e81860305e492a930e2c2691873b23be25e97e5b354ca785058e09a20025` — the same
hash the other five Joern kernels carry, because all six drive one unmodified
script, and unchanged by this expansion.

58 results: 25 `reached`, 33 `not-reached`. **Every case executed**: zero
`inconclusive`, zero `unsupported`, zero `runner-error`, 58 retained evidence
documents and zero error documents. `php2cpg` extracted every challenge
fixture — the variable method call, the variable property, the closure array,
the `use` closure, the `?\Closure` property, the anonymous classes, and the
six-hop chain — without a frontend complaint.

| Stratum | n | Correct | TP | TN | FP | FN |
| --- | --- | --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 28/32 | 14 | 14 | 2 | 2 |
| A — dispatch/reflection | 6 | 4/6 | 1 | 3 | 0 | 2 |
| B — higher-order | 8 | 5/8 | 2 | 3 | 1 | 2 |
| C — containers/paths | 6 | **6/6** | 3 | 3 | 0 | 0 |
| D — context/depth | 6 | 5/6 | 2 | 3 | 0 | 1 |
| Challenge total | 26 | 20/26 | 8 | 12 | 1 | 5 |
| **Expanded core** | **58** | **48/58** | 22 | 26 | 3 | 7 |

The classic mismatch set is **identical** to the one the previous Joern PHP
report published:

- false negatives: `dfb-taint-php-alias-propagation-positive` and
  `dfb-taint-php-exception-catch-positive`;
- false positives: `dfb-taint-php-infeasible-branch-negative` and
  `dfb-taint-php-loop-carried-negative`.

Nothing about the expansion moved the population it was added to, and those
numbers were themselves first recorded on Joern `4.0.432` and reproduced
case-for-case at the `4.0.610` pin.

Challenge mismatches, verbatim and complete:

- `dfb-taint-php-reflective-invocation-positive`: false negative.
- `dfb-taint-php-dispatch-table-positive`: false negative.
- `dfb-taint-php-function-field-positive`: false negative.
- `dfb-taint-php-callback-registration-positive`: false negative.
- `dfb-taint-php-anonymous-implementation-negative`: false positive.
- `dfb-taint-php-deep-relay-chain-positive`: false negative.

Read as approximation character, which is what stratum A is for. The engine
does **not** resolve a callee named by a run-time string (`$target->$name(...)`)
or selected from an array of closures, so both of those positives are missed
and both of their negatives are correct *for that same reason* — a true
negative arrived at by declining to resolve the call, not by refuting the flow.
It does decide `computed-property` correctly on both cells, which is a real
difference from the Joern Java kernel: Java's reflective `Field` adaptation
produced a false positive on the distinct-key negative, while PHP's native
`$holder->{$key}` is kept apart. Under-approximating dispatch while keeping
computed member identity is a coherent position, and it is one engine's
position, not a score.

Stratum B splits the same way. Closure capture is decided correctly on both
cells. `anonymous-implementation-negative` is a false positive — the
implementation merge the preregistration says that template exists to make
visible, here across two `new class implements Handler` bodies. The
`function-field` and `callback-registration` positives are missed: a closure
stored in an object property or in a hook array is not carried through to the
call site, and their negatives are again correct without the callee having been
resolved.

Stratum C is the standout: **6/6**, with `foreach` iteration over the array,
the depth-3 access path through two `__construct`-built children, and the
combined element-plus-field separation all decided correctly.

Stratum D is the preregistered prediction, confirmed. `recursive-carry` and
`context-pair-depth2` are correct on both cells; the one mismatch is
`deep-relay-chain-positive`, a false negative on the six-hop chain. The pinned
distribution's `EngineConfig` default `maxCallDepth` is **4**, verified from the
distribution itself before any fixture existed, and the chain is deliberately
six hops. The adapter did not raise that bound — no `maxCallDepth` override was
configured, so the run's identity is the documented default — and the negative
of that pair is correct *because* the engine cannot see that far. Per the
preregistration's reading rule, the pair together describes a bound, not
precision.

Normalized `witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and retains the element-by-element path evidence in
the raw document rather than synthesizing normalized witness markers. Per-case
wall clock, including cold CPG construction, ranged from 6.4 s to 20.7 s (about
12.6 minutes for the population).

### Semgrep CE 1.174.0 — `reports/semgrep-php-kernel.json`

Build identity `semgrep-oss:1.174.0`, configuration hash
`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`, unchanged:
no rule file was touched for this expansion, and the PHP rule that analyzed the
scored subset is byte-identical to the one the other ten kernels use.

58 results: 9 `reached`, 5 `not-reached`, **44 `unsupported`**, with zero
`inconclusive` and zero `runner-error`. 72 retained documents — 14 finding
documents, 14 resolved rule files, and 44 capability-decision documents — and
no error documents.

| Partition | n | Outcome |
| --- | --- | --- |
| Classic scored (`intraprocedural`) | 14 | 9 `reached`, 5 `not-reached`, **12/14** polarity match |
| Classic unsupported | 18 | capability decision from case metadata |
| Challenge unsupported | 26 | capability decision from case metadata |

The scored subset is unchanged at 14 assertions and unchanged at 12/14, with
the same two false positives every Semgrep kernel shows —
`dfb-taint-php-infeasible-branch-negative` and
`dfb-taint-php-loop-carried-negative`, the path sensitivity the pinned CLI
documents as Pro-only. **The expansion did not move Semgrep's scored population
at all**, because the scored partition is the `intraprocedural` tag and no
challenge template carries it. The `Selected` count moved from 32 to 58 and the
`unsupported` remainder from 18 to 44; nothing else moved.

All 26 challenge assertions are `unsupported` by declared capability, decided
from the case's own `feature_tags` and `expected_analysis_capability.kind`
*before* Semgrep was invoked, so not one of them reached a Semgrep process and
none can be read as a false negative. The retained reasons split as the
preregistered partition predicts: 4 name the interprocedural boundary
(`interprocedural-deep`, the deep relay and depth-2 context pairs), 4 name the
heap boundary (`heap-access-path`, the nested-path and element-object pairs),
and 18 name the general CE local/intraprocedural profile boundary (the
`reflective-dispatch`, `higher-order`, and `computed-access` cells). Every one
of the 44 `unsupported` documents also carries the PHP front end's `ga`
maturity label, which is recorded and never scored on. This is the
preregistered outcome for a bounded engine and it is correct behavior, not a
gap.

### Where the three analyzers agree, and where they do not

On the classic sixteen the picture is unchanged: both full analyzers miss alias
propagation and exception-catch on the positive side and over-approximate the
infeasible branch on the negative side, and Semgrep adds the loop-carried false
positive that Joern also shows.

On the challenge tier they disagree in *kind*, not in conclusion. Bifrost
declines 22 of 26 and decides none of them wrongly; Joern decides all 26 and
gets 20 right; Semgrep declines 26 of 26 by a rule fixed before the run. Those
are three different, defensible answers to the same question and none is a
proxy for another. The one place all three converge is the six-hop relay:
Joern misses its positive at the verified default call-depth bound of 4,
Semgrep declares the whole stratum out of scope, and Bifrost — alone among the
three — resolves it. Neither result set is evidence about any other language.

## Population boundaries

PHP results are their own population. They are never pooled with the Java,
JavaScript, TypeScript, Python, Kotlin, C#, Go, C, C++, Scala, Ruby, or Rust
kernels, never pooled with the 13-language direct-flow breadth slice, and never
averaged with a language whose core denominator is not also 29 templates. The
absence of a CodeQL PHP extractor reduces PHP's *analyzer* coverage, not its
29-template denominator, and contributes no results to any scorecard.

And, restating the rule the expansion makes easiest to violate: PHP's
32-assertion v0.3.0 core and its 58-assertion v0.4.0 expanded core are
different populations of the same name. A 17/32, a 28/32, and a 12/14 from the
older population sit beside — never inside — the 21/58, 48/58, and 12/14
recorded above.

## Reproduction

```bash
cargo run -- run-bifrost-php-kernel --bifrost /path/to/bifrost
cargo run -- run-joern-php-kernel   --joern   /path/to/joern-cli/joern
cargo run -- run-semgrep-php-kernel --semgrep /path/to/semgrep
```

Run them sequentially, never concurrently: each runner sweeps the whole report
directory at the end of its run, and two runners rewriting their own
`reports/raw/<slice>/` evidence at once race. The Joern kernel additionally
needs a host `php` interpreter on `PATH`. There is no `run-codeql-php-kernel`,
and there never has been.

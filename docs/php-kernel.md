# PHP propagation kernel

Issue #40 ports the sixteen scored Java propagation templates to PHP, as
classified in the [applicability matrix](applicability-matrix.md). The PHP cases
keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to PHP syntax. Every
scored PHP template has exactly one `positive` and one `negative` `core` case,
so the PHP core denominator is 16 templates and 32 assertions, exactly as the
matrix fixes it.

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
and requires no autoloader, `include`, or Composer manifest. Every one of the 32
fixtures passes `php -l` under **PHP 8.5.9 (cli)**, the Homebrew build installed
for this tranche. Adapters may lower the endpoints through their own models, but
the case metadata stays analyzer-neutral and reports retain only observed
evidence.

## Case population and the frozen direct pair

The PHP population is the 32 `taint`/`core` cases under `cases/taint/php/`.
Thirty were authored for this kernel with `fixture_provenance.revision`
`m2-php-kernel`. The direct-propagation pair (`dfb-taint-php-direct-positive`
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

## Analyzer coverage

**CodeQL CLI 2.26.3 — the pinned version — has no PHP support at all.** There is
no PHP extractor, no `codeql/php-*` pack, and therefore no PHP database that
could be queried. This is recorded here as *analyzer coverage*, exactly as
[the applicability matrix](applicability-matrix.md) requires. It is **never**
recorded as results: there is no `adapters/codeql/php/` pack, no
`run-codeql-php-kernel` command, no `codeql` entry in any PHP case's
`tool_model_references`, and no PHP row in any CodeQL report. An absent analyzer
produces no outcomes — not `not-reached`, not `unsupported`, not anything.

PHP's two analyzers are therefore **Bifrost** and **Joern** (#14). The Joern
adapter landed in #50 with the Java, JavaScript, and Python kernels; PHP is the
fourth language on it, and the first one for which Joern is not a third opinion
but half the total coverage.

## Bifrost selection and reproduction

The Bifrost PHP slice uses the language-qualified policy
`adapters/bifrost/policies/core-php-kernel.rqlp`, whose source and sink
selectors are `(language php (call :callee (name "dfb_source")))` and
`(language php (call :callee (name "dfb_sink")))`, with argument index 0 as the
dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-php-kernel --bifrost /path/to/bifrost
```

The command selects only the 32 PHP core assertions, materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-php-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-php-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

## Joern selection and reproduction

```bash
cargo run -- run-joern-php-kernel --joern /usr/local/bin/joern
```

The command selects the same 32 assertions runner-side (`language == "php"`,
`track == "taint"`, `score_tier == "core"`) and drives the single shared kernel
script `adapters/joern/queries/kernel.sc` with `language=PHP`, which selects the
pinned distribution's `php2cpg` frontend. One cold CPG is built per case inside
a per-case scratch root, and the retained evidence document is written to
`reports/raw/joern-php-kernel/<case id>.json`.

`php2cpg` shells out to its bundled PHP-Parser
(`/opt/joern/joern-cli/frontends/php2cpg/bin/php-parser/php-parser-4.15.10.phar`),
which is itself a PHP program, so **a host `php` interpreter must be on `PATH`**
for this kernel to run at all. The observed interpreter was PHP 8.5.9 (cli),
Homebrew. Without it the frontend fails and the script's own `catch` retains a
`runner-error` document — an unavailable frontend can never look like a negative.

The endpoint identifiers are read out of each fixture's own `DFB-SOURCE:` and
`DFB-SINK:` marker lines, never assumed, exactly as for the other three Joern
kernels.

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

Both retained snapshots cover all 32 PHP core assertions, at fixture revision
`sha256:9630d095eb41e3d6c1aef8423e8d4381c6c601ceefb9146b5b42bc14f94ad612`. They
are separate populations and are not pooled with each other or with any other
language.

### Bifrost, `reports/bifrost-php-kernel.json`

Bifrost 0.10.5, build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`.
Configuration hash
`eff9c5d510d5ee7670b55350b72f5d15a87b536fe961870910a44eb75c8b5d59`; it covers
both `core-php-kernel.rqlp` and the breadth `core-direct.rqlp`, because the
frozen direct pair is evaluated through the policy it declares.

32 results: 10 `reached`, 8 `not-reached`, and 14 `inconclusive`, with zero
`unsupported` and zero `runner-error`. **17 of the 18 decisive outcomes match
the expected polarity; 17 of 32 assertions.**

Eight template pairs are decisive on both halves and correct on both: direct
propagation, local overwrite kill, the local multi-step chain, call-context
separation, argument-position separation, the one-hop and two-hop return relays,
and branch join. The infeasible-branch pair is also decisive on both halves, but
its negative is wrong.

The single decisive mismatch is a false positive:

- `dfb-taint-php-infeasible-branch-negative` — Bifrost reports a flow through an
  `if (false) { ... }` body. This is the same over-approximation its Go kernel
  shows on the same template, published as observed rather than tuned away.

The 14 `inconclusive` results are capability evidence, never negatives:

- ten retain `capability_incomplete` with "procedure value-flow snapshot ... is
  unsupported (assignments)" — the complete heap/separation stratum (object
  separation, same-object field separation, alias propagation, array element)
  and the exception-catch pair, both polarities each;
- four retain `partial_discovery` with "procedure value-flow snapshot ... is
  unknown" — the arithmetic-expression pair and the loop-carried pair. The
  loop-carried pair additionally carries a "Controlled input reaches the
  benchmark sink" finding, which under an incomplete analysis is not a decisive
  outcome and is not scored as one.

All 32 raw Bifrost JSON reports are retained under
`reports/raw/bifrost-php-kernel/`. Per-case wall clock ranged from 37 ms to
78 ms (1.9 s for the population), far inside the 60-second `execution_budget`.

### Joern, `reports/joern-php-kernel.json`

Joern 4.0.432, build identity `joern-cli:4.0.432`, `php2cpg` frontend over PHP
8.5.9 (cli). Configuration hash
`2ce582b8a5d1efd4e6025153893178bfb900cce933826826d63371d632a64564` — the same
hash the other three Joern kernels carry, because all four drive one unmodified
script.

32 results: 16 `reached` and 16 `not-reached`, with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes, 32 retained evidence documents and
zero error documents. **28 of 32 match the expected polarity.**

The four mismatches:

- false negatives: `dfb-taint-php-alias-propagation-positive` and
  `dfb-taint-php-exception-catch-positive`;
- false positives: `dfb-taint-php-infeasible-branch-negative` and
  `dfb-taint-php-loop-carried-negative`.

That is exactly the mismatch set Joern's Java and Python kernels show, template
for template: aliasing through a field and value transfer to an exception
handler are missed, and the infeasible branch and the loop-carried kill are
over-approximated. A shared engine over a fourth language-specific frontend
reproducing the same four failures is the expected shape. No fixture was
changed, no query was contorted, and no case was special-cased to move a result.

Normalized `witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and retains the element-by-element path evidence in
the raw document rather than synthesizing normalized witness markers. Per-case
wall clock, including cold CPG construction, ranged from 4.7 s to 14.4 s (about
4.4 minutes for the population).

### The two analyzers agree on where PHP is hard

Both adapters miss alias propagation and exception-catch on the positive side
and over-approximate the infeasible branch on the negative side. They differ in
kind rather than in conclusion elsewhere: Bifrost declines the whole heap
stratum as incomplete where Joern answers it — correctly in seven of those eight
assertions, missing only alias propagation's positive — and Joern decides the
arithmetic-expression and loop-carried pairs where Bifrost's discovery is only
partial. Neither result set is a proxy for the other, and neither
is evidence about any other language.

## Population boundaries

PHP results are their own population. They are never pooled with the Java,
JavaScript, TypeScript, Python, Kotlin, C#, Go, C, C++, or Rust kernels, never
pooled with the 13-language direct-flow breadth slice, and never averaged with a
language whose core denominator is not also 16 templates. The absence of a
CodeQL PHP extractor reduces PHP's *analyzer* coverage, not its 16-template
denominator, and contributes no results to any scorecard.

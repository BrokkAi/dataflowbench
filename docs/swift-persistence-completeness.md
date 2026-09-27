# Swift persistence completeness work

The prior suite-state prototype strongly cleared a key whenever a receiver had
any SSA origin in that suite. A receiver selected between two different suites
therefore cleared both, although runtime execution writes only one. The new
preregistered control reproduces that false clean result at sink line 70.
All thirteen earlier branch/alias/domain/order controls remain present.

The isolated `6.8.4-dfb.9` runtime separates possible stores from proven clears.
Stores still update each possible domain. Clearing requires all discovered
initializer origins to resolve to the same literal Foundation.UserDefaults
suite and no unsupported reaching CFG/SSA leaf. Unknown definitions or values
propagate incompleteness; they cannot authorize strong clearing. The traversal
uses typed definition, phi-input, pattern-binding and forced-value relations.
It does not infer identity from source text or names alone.

The baseline observation has exactly six flows, missing required sink 70.
The repaired observation has exactly seven: 13, 16, 29, 37, 43, 61 and 70 from
source line 12. Same-domain phi sink 78 and all prior negative sinks remain
absent. Receiver proof rows at line 68 contain both suites with `must=false`;
line 76 contains one suite with `must=true`. Both have complete discovered
origins in this control. Actual clear rows exclude line 68 and include line 76.

The two independent extractions completed in 102.935 and 89.477 seconds.
All eight baseline and nine repaired queries and decodes completed. Raw failed
semantics are retained alongside the repair; the baseline is never reclassified
as clean or overwritten. Portable mutation tests reject a missing mixed flow,
a false same-suite flow, a mixed strong clear, a lost same-suite clear, a forged
must proof, a missing domain, and a vendor-native relabel.

This is still non-scored adapter evidence. The complete-origin field covers
receiver provenance, not whole-function persistence effects. A typed
applicability gate for unknown mutations, unsupported preference operations,
dynamic keys/suites and unqualified payload types remains required before
production integration. No current empty result outside admitted controls is
clean evidence. Aggregate resource containment and whole-profile semantic
completeness remain unproven; the immutable 104-entry population and historical
reports are unchanged. Issues #220 and #215 remain open.

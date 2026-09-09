# Recursive composition preregistration

Issue #168; preregistered 2026-09-09 before fixture results. These additive
identities are eligible only for a future freeze (v0.8.0 or later). Existing
population manifests, fixtures, reports, and frozen denominators are immutable.
This document specifies intent; it makes no analyzer accuracy claims.

## Common construction

All cases are taint/core/benchmark-controlled balanced pairs. Use depth 3,
constant and nonzero, with source and sink outside the recursive component.
Use integer payloads and addition by 1 for portable payload transformations;
no overflow is reachable. A clean value is 0. Recursion must carry the queried
payload or effect; never add an irrelevant recursive wrapper. Use fixture-local
source/sink functions and standard language constructs, no external libraries.
Keep a source-backed path live in negatives. Every fixture has DFB-SOURCE and
DFB-SINK anchors plus DFB-WITNESS checkpoints at recursive transfer, base case,
and the defining composed operation. Negatives mark the killing assignment
DFB-KILL. The sink is called only after the operation being tested completes.

Use the template suffix below as the case directory/scenario stem. Template IDs
are `dfb-template-chal-<suffix>`; capabilities are `<suffix>-taint`. Negative
mechanism is `overwrite-kill`. Common dimensions are recursion,
interprocedural-flow, and flow-sensitivity; add heap-field-sensitivity for heap
and exception templates, and exceptional-flow for exception. Use existing
schema tags `recursive` plus applicable existing operation/dispatch tags; do not
invent a schema value silently. All semantic adaptations must be documented.

## Templates

1. **recursive-payload-transform**: `walk(v,n)` computes `next=v+1`, calls
   `walk(next,n-1)`, then returns the recursive result plus 1. Base returns v.
   Negative base assigns v=0 before returning; unwind adds 1 only to that clean
   result. Tests both descent and non-tail return operations on the payload.
2. **mutual-recursive-transform**: two distinct functions A and B alternate
   calls, each adding 1 to the payload before transfer and to the returned
   result afterward. Both have a base case; both negative bases kill v. Start
   at A with depth 3, so the base is in B. Tests a two-procedure recursive SCC,
   with the same live positive/negative call topology.
3. **recursive-heap-unwind**: caller creates one box with integer field value.
   `walk(box,v,n)` recurses first; base writes v to box.value. Each non-base
   frame then assigns box.value=box.value+1. Negative base writes v then
   overwrites the same field with 0. Caller sinks box.value after return. This
   tests caller-visible recursive effects and loads/stores while unwinding;
   use an actual shared object/reference/pointer, never a copied value struct.
4. **recursive-callback-transform**: `walk(v,n,step)` uses a callable parameter
   to call a separate `step(v,n-1)`; step transforms v+1, calls walk with itself
   as callback, and transforms the returned result +1. walk's base returns v;
   negative base kills v. Start walk(source,3,step). The cycle crosses a real
   indirect callable invocation (function pointer in C/Rust; equivalent
   callable/interface in other languages), not a direct call decorated with
   an unused callback. Type declarations must express the cycle legally.
5. **recursive-exception-persistence**: recursive descent forwards box and v.
   Base writes v to box.value and throws a fixture-private exception; negative
   base overwrites the field with 0 before throwing. The exception propagates
   through all recursive frames to an outer catch; after catching that exact
   signal, caller sinks box.value+1. Do not catch inside recursive frames or
   add a normal recursive return path that bypasses the exceptional transfer.

## Applicability

| Languages | Payload | Mutual | Heap unwind | Callback | Exception |
| --- | --- | --- | --- | --- | --- |
| Java, JavaScript, TypeScript, Python, Kotlin, Scala, C#, PHP, Ruby, C++ | direct | direct | direct | direct | direct |
| Go | direct | direct | direct | direct | adapted: private panic signal and recover |
| C | direct | direct | direct | direct | inapplicable: no typed exception unwinding |
| Rust | direct | direct | direct | direct | inapplicable: panic is not guaranteed typed recoverable transfer |

Go must recover only the exact private signal and re-panic other payloads.
C error codes and Rust Result are distinct semantics and cannot stand in for
this exception identity. No reflection or name-based dispatch is required.
The initial suite has 63 pairs / 126 assertions across 13 languages. It does
not claim tree recursion, unbounded depth, recursive alias separation, or a
full cross-product of all operations.

## Delivery and validation

Coordinator owns this specification, shared schema/harness changes, rollout
registration, and cross-language integration. Each language task owns only its
new fixture directories and language-specific documentation/validation files.
Workers must not edit existing frozen fixture bytes or reports. They report
any shared adapter registration needed to the coordinator. Register new core
identities atomically with their language fixtures at integration; do not
weaken population validation or admit partial pairs.

Compile or syntax-check both polarities and check metadata/markers. Validate
that transformed positive outputs depend on source and negatives do not, using
bounded executable checks where practical. Real analyzer outcomes are separate
from executable fixture checks: retain unsupported/inconclusive states. Native
analyzer runs require configuration provenance and are not a prerequisite for
inventing a supported verdict. CI must be checked live and failures fixed.

# A39 — 2026-09-22: Swift Result failure-path extension

Prospective adaptation of `dfb-template-result-error-propagation` for #220,
separate from core exception transfer. No existing freeze is invalidated and
no existing fixture, population or evidence is rewritten. This contract precedes
its fixture and analyzer-partition commits.

## Canonical meaning and Swift construction

The existing Rust extension carries a source integer in `FlowError.value` inside
`Result::Err`, propagates the failure through a helper call with `?`, then reads
the field in the outer failure branch. The negative retains that computation
but sends an unrelated clean value to the sink. Swift preserves the failure
payload and early-return control path using explicit `switch`; it does not
claim a Swift `?` operator, throw/catch transfer, or core exception-catch support.

Use standard-library `Result<Int, FlowError>`, with fixture-private
`struct FlowError: Error { let value: Int }`. A nonthrowing producer evaluates
`dfb_source()` and returns `.failure(FlowError(value: input))`. A relay switches
on the producer's result: `.failure(let error)` returns `.failure(error)`
immediately, while `.success(let value)` returns `.success(value)`. An outer
switch sends `error.value` to `dfb_sink` only in the failure branch. Both
polarities retain producer, relay, both enum arms and the complete failure
payload path. The negative changes only the sink argument to a clean local
initialized beside the source-dependent computation.

[`Result.failure`](https://developer.apple.com/documentation/swift/result/failure(_:))
stores the failure value, and Swift's
[enumeration pattern matching](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/enumerations/)
binds associated values in a switch. These operations preserve the canonical
failure-payload propagation question. The spelling of early propagation differs
from Rust and remains explicit in every comparison.

## Pair and evidence requirements

- Case IDs: `dfb-taint-swift-result-error-propagation-positive` and `...-negative`.
- Template: `dfb-template-result-error-propagation`; tier `language-extension`;
  track `taint`; profile `benchmark-controlled`.
- Expected flow/nonflow follows source dependence; negative mechanism is
  `unrelated-value`. Place exact source/sink anchors and witness markers on
  failure construction, relay failure return, and outer payload consumption.
- No modeling declarations, custom operators, optional coercion, `try`, `throw`,
  `fatalError`, or trap-based substitute supplies the propagation.
- Compile/link both under the existing witnessed Swift pin; non-scored concrete
  controls inject source values 7 and 19 and verify the positive changes with
  the source while the negative stays clean. Concrete execution does not qualify
  analyzer correctness.
- Preserve the 512 MiB / 60 second analyzer budget. Preregister each adapter's
  exact extension selection before execution; require resolved endpoint identity
  and preserve incomplete, unsupported, resource and runner-error outcomes.
- Add these cases to a new prospective population identity. Do not edit
  `swift-synthetic-v1`, its 90 cases, or any prior report/configuration artifact.
  The two extension rows never change core or controlled-model denominators.

This amendment establishes the intended pair contract only. The identity
remains unresolved in the coverage inventory until the pair and independent
execution evidence are delivered. It supplies no release or qualified score.

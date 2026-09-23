# Swift opaque propagator Objective-C runtime amendment

**Date:** 2026-09-23  
**Decision:** Prospective, narrowly scoped exception for the two template IDs below.

## Scope

The Swift kernel remains synchronous, standard-library Swift under its existing
scope. This amendment authorizes implementing and testing a prospective Darwin-only construction that
explicitly uses Foundation and the Objective-C runtime for:

- `dfb-template-model-opaque-propagator`
- `dfb-template-model-propagator-position`

The candidate shape is an `NSObject` subclass with declared `@objc dynamic`
methods, selecting a declared method on `self` by runtime selector and invoking
it through the Objective-C runtime `perform` interface. The position template
must use the same opaque self-dispatch shape for a two-argument method, with
its positive tainting the second argument and its negative tainting only the
first. This describes a candidate contract for review; it does not assert that
the construction has demonstrated semantic fidelity or analyzer support.

This exception does not add Objective-C runtime dispatch to the Swift
reflective-invocation challenge, other templates, or the general Swift language
scope. It does not authorize arbitrary hidden helper bodies or a broader
reflection exception.

## Qualification remains required

Authorization to investigate this construction does not qualify either
fixture or activate either model. Before scoring, the follow-up must establish:

- semantic fidelity to the existing declared-method reflective self-dispatch
  contract, including method identity and return behavior;
- runtime correctness on the stated Darwin/Foundation/Objective-C runtime
  platform;
- resolver evidence for the exact declared selector, owner, signature, and
  parameter/return positions;
- independent activation controls showing each model is load-bearing, with
  model-off and model-on behavior;
- for the positional template, second-argument propagation and first-argument
  near-miss controls, including rejection of propagation from position 0.

Failure or incomplete evidence leaves the affected template unqualified and
its result incomplete. Unsupported or deferred classifications require their
own justified evidence; this exception does not authorize them automatically. A model-on
success alone is not sufficient evidence of fidelity or load-bearing activation.

## Historical record and population

This is prospective. Preserve the prior standard-library scope, historical
fixture populations, denominators, and published results as recorded. Do not
rewrite or replace historical fixtures or results to make them appear to have
used this exception. Any later fixtures and population must be immutable and
versioned as a new prospective population, with this amendment and its platform
scope recorded in their provenance. This amendment alone does not qualify a fixture or result.

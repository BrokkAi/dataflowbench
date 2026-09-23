# Darwin Objective-C opaque propagator prototype

The dated amendment authorizes this construction for only the opaque propagator
and positional propagator templates. The non-scored prototype declares methods
on an NSObject subclass, assembles a selector string at runtime and invokes the
method on self through perform. It preserves declared-method self-dispatch;
there is no hidden implementation or added barrier.

The runtime harness enumerates methods declared directly on Opaque, verifies
the exact selector owner and Objective-C signatures, and checks return values.
Both carry and block propagate at runtime. The block negative is intentionally
an undeclared sibling: it checks member-specific model activation, not runtime
sanitation. The two-argument method returns only its second argument.

Runtime execution passed after a committed preregistration. The compiler,
SDK, source, binary and bounded phase records are hashed. Runtime and analysis
controls contain identical dispatch-class bytes. The preliminary compiler-only
failure (SDK return-pointer optionality) is retained separately.

The first analyzer attempt extracted exact wrapper signatures but recognized
no endpoints. A retained diagnosis proves the top-level calls have resolved
static targets but no data-flow nodes. Their empty flows are inconclusive, not
opacity evidence. A second prospective control moves the identical call
sequence into an explicit function, as existing benchmark controls do. Queries,
model positions, class implementation and expectations remain unchanged.

The declared model binds the exact Swift module, wrapper owner, member, arity,
instance method kind and Swift.String parameter/return types. It models carry
argument 0 and select argument 1 only. Both lanes must reach a direct baseline;
the model-on lane must additionally reach carry and the second-position call.
The undeclared sibling, first-position call and clean carry must remain absent.
No barrier is introduced to force opacity.

Runtime selector evidence and static wrapper binding are distinct: this does
not claim the analyzer resolved the target of dynamic perform. No population,
score, release, general reflection exception or whole-profile qualification is
activated by this prototype. Aggregate memory compliance and semantic
completeness remain unproven.

## Observed activation

The function-scoped extraction and all three queries completed. Both lanes
reach the direct baseline at line 27. Only model-on reaches carry at line 28
and the second-position call at line 30. The undeclared block at line 29,
first-position call at line 31 and clean carry at line 32 remain absent.
All seven resolved wrapper/parameter rows match the declared bindings.

Seven runtime and nine activation/provenance tests enforce these observations
in CI. These are independent prototype controls; canonical fixtures, prospective
population registration, other analyzer outcomes and release integration remain
separate work. The pinned extractor's missing top-level CFG-node evidence is
retained as a capability limitation, not an unsupported-template decision.

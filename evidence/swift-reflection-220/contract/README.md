# Non-scored reflection fidelity and opacity investigation

Preregistered 2026-09-22 for #220 before probe execution. This does not amend
opaque template semantics or add a registry case. The candidate uses `Mirror`
to select a stored closure by runtime child label, casts it to its exact
function type and invokes it. It tests reflected function-value dispatch,
which may differ materially from reflective declared-method self-dispatch.
A successful probe is evidence for review, not permission to reuse template IDs.

Controls retain carry, no-flow sibling block, and second-position select.
Positive/negative source inputs and direct-flow controls test source/sink
identity. Native model-off and model-on outputs are recorded independently for
CodeQL and Joern, under their existing pins, with exact resolved signatures.
On mode declares carry argument0->return, block no-flow, select argument1->return.
No source-text recognition or AST approximation establishes semantic identity.

Probe deadline may be 180 seconds as in existing non-scored activation probes;
this does not change registry budgets (512 MiB / 60 seconds). All commands,
inputs, native output, failures and environment identity are retained in fresh
attempt directories. A native empty flow set is not proof of completeness or
universal opacity. Concrete compilation/execution only tests fixture behavior.

# Swift resolved native adapter experiments

This prospective adapter lane addresses the append and conversion applicability
failures retained in the original native controls. It does not modify those
controls, their observations, the stock runtime, or the historical benchmark.
All observations are non-scored; aggregate memory compliance and whole-profile
semantic completeness remain unproven. Issues #220 and #215 remain open.

## Append

The pinned generic taint library exposes `InputSig` and `TaintFlowMake`.
The experiment delegates the stock language semantics except for an additional
append heuristic edge whose resolved method fails the existing exact
Swift.String `append(_:)` predicate. It does not introduce a node barrier.
Stock summary edges and ordinary method-body data flow remain available.
This is a bounded String append experiment, not qualification of every append
operation in the SDK. Internal Swift language bridges are pinned dependencies.

Three preregistered packages retain the progression:

| Package | Stock assisted lane | Resolved experiment |
| --- | --- | --- |
| Original independent control | real flow plus constant-body wrong-arity false flow | real flow only |
| Extended ordinary-body control | real, wrong-arity, and local body flows | real and local body flows |
| Unchanged canonical pair | positive flow; negative no flow | positive flow; negative no flow |

The extended control also retains safe constants and a wrong-owner lookalike.
A local `Carrier.append` passes input through its actual body; its positive flow
survives while its safe-literal counterpart remains clean. The first query pack
had an ambiguous module-name warning; the next version resolves that warning
without rewriting the first run. Canonical sources join the immutable population
and retain their source archives. Vendor-native observations remain separate.

Evidence, plans, copied queries, commands, measurements, and archives are under
`evidence/swift-resolved-native-v1`. Analysis requests retain 60 seconds and
2048 MiB; extraction retains the prospective 150-second limit. Successful
commands do not establish aggregate memory containment.

## Conversion summary applicability

The pinned stock summary interpreter can attach Data conversion summaries to
local lookalikes. Summary attachment also changes body dispatch, so merely
removing a taint edge cannot establish restoration of ordinary body semantics.
The isolated library experiment restricts four conversion catalog selectors by
resolved defining module, nominal owner/module, and arity. Unrelated catalog
rows remain stock. It is labeled adapter-patched, never vendor-native.

The materializer checks all 3398 original runtime files, applies a hash-bound
patch to a copied pack, assigns a distinct library version, removes the stock
build identity, and checks every other copied file. The query lock and recorded
library-path resolution bind that distinct version. The stock tree is unchanged.
The first sandbox attempt could not verify process cleanup. Its elevated retry
exposed an unbound QL string parameter compilation error. Both are retained;
patch revision two adds the required binding declaration before a new run.

The retained-database conversion experiment is only an initial applicability
control. Independent direct initializer heuristics and positive local method
bodies require additional controls before qualification. Sanitizer, keyed
persistence, Joern provenance, opaque-template fidelity, complete prospective
execution, and release gates remain separate dependencies.

Revision two completed all seven queries and decodes within their bounds.
The real and safe chains retain all eight manual summaries, ten port rows,
six simple transfer edges, and four content stores. All four local calls are
unmodeled and have no summary ports or transfer/store edges. The only endpoint
flow is source 12 to the real sink 17; the original local false flow to sink 27
is absent. This is an initial applicability result, not a whole-family pass.

Portable checks: `python3 scripts/verify-swift-resolved-append.py` and
`python3 scripts/verify-swift-resolved-conversion.py`. Their mutation suites
reject lost positive flows, local false flows, provenance changes, missing
content stores, source changes, profile relabeling, and scored promotion.

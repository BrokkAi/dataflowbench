# Swift UserDefaults qualification: blocked independent control

Before the canonical persistence pair, an independent function-wrapped control
compares direct raw flow, real UserDefaults write/read using the same literal
key, a different initialized key, and a local constant-body UserDefaults owner.
Both real keys are initialized clean before the raw payload write. Expected
assisted flows reach only the direct sink and real same-key sink. Fixture
binaries are never executed; the control does not mutate live preferences.

Observations keep resolved declaration modules, nominal owners, selectors and
arity separate from literal keys read through native StringLiteralExpr nodes.
No production rule is approximated by source matching or key-name heuristics.
Attached manual ports, instantiated simple/read/store summary relations, and
endpoint flow remain separate. A real positive without proven engagement and
separating controls cannot qualify the family.

The preregistration binds source, queries, selected vendor source and runner
closure before extraction. CodeQL 2.27.1 / swift-all 6.8.4 and Swift 6.3.3 / SDK
26.5 use 150 seconds for extraction and 60 seconds / 2048 MiB per diagnostic
query. Aggregate memory compliance and semantic completeness remain unproven.
Vendor-native and adapter-assisted observations stay separate and non-scored.

Missing real positive flow or model engagement is a scoped qualification
blocker, not evidence of clean behavior or proof the entire tool is unsupported.
No custom keyed model, suppression or changed fixture semantics is supplied.
Append, sanitizer and summary blockers remain independent. No full-corpus run,
scored activation, freeze or publication is part of this scope.


## Retained result

The independent control is **blocked**. The canonical persistence pair remains
unrun. Portable checks validate the retained failure; CI success does not
qualify persistence semantics or activate scores.

| Control | Assisted endpoint flow |
| --- | --- |
| Direct raw baseline | source 12 → sink 13 |
| Real same-key UserDefaults write/read | **missing at sink 16** |
| Real other initialized key | none |
| Local constant-body owner | none |

All nine calls resolve: six to Foundation.UserDefaults, three to the fixture's
local UserDefaults. Seven key arguments are retained as native StringLiteralExpr
values. The real raw write and same-key read both use `payload`; the other-key
read uses `other`. Both keys' clean initialization is witnessed separately.
Thus the missing same-key positive is not a missing source/sink baseline or
an unresolved literal-key selection.

All nine scoped manual-model flags are false. The attached manual-port and
instantiated simple/read/store-edge queries return empty sets. This is a scoped
absence of the requested model engagement, not a whole-tool unsupported claim
or proof that every possible modeling mechanism is absent. The copied vendor
cleartext-storage rule recognizes a write sink; that is not a keyed persistence
transfer into a later read. No substitute model is added.

The vendor-native lane has no source or flow; each lane has eight sink nodes,
and the adapter-assisted lane has one environment source. Successful extraction
took 89.670 seconds. All seven queries and their decodes completed within their
preregistered limits. No fixture binary was run and no follow-up extraction or
query correction was needed.

The raw attempt, source archive, queries and preregistration are under
`evidence/swift-persistence-qualification-v1`. Run
`python3 scripts/verify-swift-persistence-control.py` and
`python3 scripts/test-swift-persistence-control.py` for portable verification.
Mutation checks reject changed key provenance, missing baseline evidence,
invented model engagement, or scored promotion. Existing append, sanitizer and
summary blockers remain independent; memory compliance and semantic
completeness remain unproven.

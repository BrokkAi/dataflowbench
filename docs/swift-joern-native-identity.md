# Joern Swift native-property binding blocker

Joern **4.0.633** exposes insufficient property identity in the compiler-backed
CPGs of these controls to admit the requested environment/argv/Process setter
profile. This is a concrete binding gap in the inspected native graph. It is
not a claim that Swift analysis is impossible or that every Joern model API
lacks the capability.

## Exact reproducer and native observations

`evidence/swift-joern-identity-220/control/main.swift` reuses the real and
lookalike function control from the verified CodeQL source profile. Its second
variant, `control-unqualified/main.swift`, moves local ProcessInfo/CommandLine
lookalikes into an enum and accesses the real imports without module qualifiers.
Neither executable nor function is run. Both compiler checks, compiler-backed
frontend imports, and native graph queries completed successfully. Each
frontend log records a type map and parsed CPG, with no warning/error entry.

The query dumps native node properties and REF, CALL, AST, RECEIVER, EVAL_TYPE,
and BINDS relationships. No source or sink classifier, flow semantics,
source-text resolver, or graph repair is applied. Source lines and field names
locate reproducer observations only; they do not establish production identity.

| Native field access | Module-qualified variant | Unqualified variant |
| --- | --- | --- |
| ProcessInfo.environment | `ANY`, no REF | `__C.NSProcessInfo`, no REF |
| CommandLine.arguments | `ANY`, no REF | `Swift.CommandLine`, no REF |
| Process.arguments setter | `__C.NSTask`, no REF | `__C.NSTask`, no REF |

The unqualified types identify owners, not the required returned dictionary or
array values. The calls link to the generic `<operator>.fieldAccess` method,
not to external property declarations/getters/setters. The native graph does
not supply the declaration/owner/module/value-type proof required by this
adapter contract. Source spelling and inferred owner names cannot fill that gap.

The graphs are not empty: local OtherOwner properties have native REF edges to
MEMBER nodes, and the real Process.run call retains the compiler-derived
`cobjc:(cs)NSTask(cm)launchedTaskWithExecutableURLargumentserrorterminationHandler`
identity and a corresponding callee edge. Some local member type strings are
also imprecise (for example `Foundation.URL` for a dictionary property). A REF
edge alone is therefore not a complete source identity/type certificate.
The static-run observation does not establish a complete source/sink profile.

## Reproduction and limits

`probe.py` and `probe-unqualified.py` retain the exact commands, source and
script copies, runtime hashes, scratch locations, build logs, graph JSON, and
phase outcomes. Use their explicit local tool paths or supply the same pinned
artifacts at those paths. They require an unused attempt directory and never
replace an existing attempt. Plans were written before each execution.

Both attempts request **512 MiB** of Java heap and retain **60-second**
queries/typechecks plus the previously authorized **180-second non-scored
frontend diagnostic** limit. The CodeQL 2048-MiB amendment does not apply.
Observed typecheck/frontend/query durations were **1.85/2.35/3.88 seconds** and
**1.41/1.69/3.38 seconds**. Query command maximum RSS was **412.66 MiB** and
**391.45 MiB**. These remain unqualified diagnostics: heap requests and command
RSS do not prove aggregate process memory or semantic completeness.

Run `python3 scripts/verify-swift-joern-identity.py` and
`python3 scripts/test-swift-joern-identity.py` to verify the immutable evidence,
phase bounds, missing external bindings, and working local/member and native
call controls. Mutation tests reject vacuous graphs and invalidate the retained
blocker when an external binding or observed type changes.

## What must change before admission

The frontend/native graph must expose resolver-backed external property
bindings: exact declaration and module/owner identity, getter/setter association
and staticness, and the property value type (including collection element types).
Those identities must distinguish real environment/argv/Process properties from
module-local, nested, wrong-owner, and wrong-type lookalikes. Actual indexed
positive and negative flow controls would then qualify the adapter profile.
Generic FullNameSemantics mappings do not supply those missing bindings.

The prospective admission is **blocked on unresolved native endpoint identity**.
No corrected Joern profile, new unsupported partition, normalized `Unsupported`
result, or score is emitted. Any future prospective `Unsupported` decision must
follow the existing capability contract and its own scoped evidence; this
runtime observation does not rewrite earlier reports or broaden their claims.
No upstream issue was posted. Integration, opaque selection, and release work
remain separate under #220 and #215.

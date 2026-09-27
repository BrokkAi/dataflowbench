# Exact staged opaque fixture qualification

The prospective runner executes the four staged `swift-opaque-v3` source files
serially under CodeQL 2.27.1, swift-all 6.8.4, Swift 6.3.3 and SDK 26.5.
Its preregistration binds source, population, queries, library manifest, compiler,
extractor, SDK settings, extraction policy and runner helpers before extraction.
It uses the already qualified declaration-based opaque model unchanged.
Fixture binaries are compiled for extraction and never executed by this runner.

The evidence binder independently checks the retained artifact closure, each
case's source digest, the actual archived extraction source, extractor logs,
command/decode records, resolved wrapper signatures, exact endpoint anchors and
model-off/on flow rows. It derives the observation before calling the conservative
v3 result boundary. No caller-provided `qualified` field enables a result.

A positive must have exactly its source-to-sink row under model-on and none under
model-off. Each negative must retain both endpoints and its declared wrapper
identity with no endpoint flow under either profile. The prototype's independent
direct-flow baseline remains separate evidence; these canonical source bytes
are not modified to add diagnostic calls. Static wrapper binding still does not
claim resolution of the dynamic Objective-C `perform` target.

The diagnostic extraction limit is 150 seconds and analysis is 60 seconds with
2048 MiB requested. The canonical contract remains 60 seconds / 512 MiB. Neither
requested limits nor recorded process RSS prove aggregate containment. The
normalizer therefore retains every semantic observation as inconclusive when
execution succeeds; failures retain runner-error and their artifacts. This is
exact-fixture semantic evidence, not scored activation, canonical registration,
resource qualification, a freeze, or publication.

Reproduce the portable binding and regression checks with:

```sh
python3 scripts/test-swift-opaque-v3-evidence.py
python3 scripts/verify-swift-opaque-v3-evidence.py
```

Native reruns require a new output directory and the exact assets named in
`adapters/codeql/swift-opaque-v3/plan.json`; never overwrite an attempt. Unknown
cleanup stops the serial runner and leaves remaining selected cases explicit.

## Retained first attempt

`evidence/swift-opaque-v3/attempt-01` completed all four extractions and all
roles/flow/identity queries and decodes. Both positives have exactly one
model-on flow and no model-off flow. Both negatives retain their exact endpoints
and wrapper identities with no flow in either lane. The independently recomputed
`attempt-01-observations.json` preserves raw reached/not-reached evidence and
four inconclusive normalized rows with `ResourceContractMismatch` and
`AggregateResourceQualificationUnavailable`. No resource-compliant result or
canonical population registration is established.

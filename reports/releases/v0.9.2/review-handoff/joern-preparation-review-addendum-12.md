# Joern preparation review addendum 12

Recorded `2026-10-25T20:13:40.441958Z`. This append-only handoff records the one actual native-controls04 partial invocation after the corrected exact-review02 and fresh admission. It preserves the failure and its evidence limits; it does not claim qualification, an engine result, Joern05 completion, release, or publication.

## Corrected review and admission

The request remained [`native-control-request-04.json`](../qualification/joern-post-bifrost-01/native-control-request-04.json), SHA-256 `e5fef8bf3a9d3b234c88f0b36731f5231ddde9dac044aa4029555780908459ea`, bound to source HEAD `76e6121651e94be113fd0d5f027419f7d0f0859b` and 2,335 source refs. The source-commit check remained [`native-source-commit-request-check-04.json`](../validation/joern-post-bifrost-01/native-source-commit-request-check-04.json), SHA-256 `9b32aca234f597be23395f278dc400b9a0ae005189f035cda843eba322ef719d`, with 109 ledger rows, full pending 108-case schema return, zero pending process dispatches, and no inferred qualification.

The first exact invocation receipt, SHA-256 `cfa0474040dcaa5f1fbc9c57b4d7787f20eb91922306e01822e1cadd80a9a496`, was rejected before admission because its `resources_sha256` contained a one-character binding typo. The binding-stop receipt is [`native-controls04-review-binding-stop-01.json`](../validation/joern-post-bifrost-01/native-controls04-review-binding-stop-01.json), SHA-256 `8f4c177138616cd27a97e2f5b73fcd0ea805335763aa561a82dda5ce9301496c`. No resource sampling, lock, namespace, bootstrap, JVM, engine, analyzer, or attempt occurred under that rejected document.

The corrected exact review is [`native-controls04-exact-invocation-review-02.json`](../validation/joern-post-bifrost-01/native-controls04-exact-invocation-review-02.json), SHA-256 `0fd14dcc585cfab28fc1c2331602f7a57320a36193da8ae483827c33c08a4d3c`. Its private command artifact `/private/tmp/joern05-native-controls04-exact-command-02.json` is SHA-256 `bf16e786123236b6e819998023f39cd388cc094915592f0176c33d5a32148d19`; it binds review02 and the same seven canonical inputs. Canonical `validate_review` checked all seven bindings after the receipt write and passed; the review remained limited to one later native-control qualification bootstrap after fresh admission, with no qualification or publication authority. Fresh admission [`native-controls04-fresh-admission-02.json`](../validation/joern-post-bifrost-01/native-controls04-fresh-admission-02.json), SHA-256 `adf53a0e082e29affd672744e12cf18e28033e335b20ebde37e0efd7f0f2ebd2`, passed read-only with 271,214,202,880 free bytes, zero contenders, a closed graph, existing common lock, absent namespace, no engine invocation, and no bootstrap. It took 32.950138208980206 seconds.

## Actual native-controls04 stop

The corrected bootstrap was invoked once at `2026-10-25T20:01:28.704443Z`. Parent PID 93055 and keepawake PID 93057 were born at `Sun Oct 25 22:02:38 2026`; worker PID 95468 was born at `Sun Oct 25 22:03:50 2026`. The worker live check verified the environment, argv, interpreter, ownership, flock, and full pending 108-case validator before entering controls.

The run reached `ready` and `controls-started`, then stopped at `2026-10-25T20:06:15.345587+00:00` with a generic `ValueError: foreign analyzer/heavy contender`. The sealed root post-stop check was recorded at `2026-10-25T20:09:07.860883+00:00`. The sealed exit receipt is [`exit.json`](../qualification/joern-post-bifrost-01/native-controls-04/exit.json), SHA-256 `ea947b6a881e8ef105ecd29715019a80cc45dbd5f7c4f7af37713787155ba6dd`; the root stop receipt is [`native-controls04-root-stop-check-01.json`](../validation/joern-post-bifrost-01/native-controls04-root-stop-check-01.json), SHA-256 `6d8958898aacaa53e6affb6708f1e3bcf2c008c0d33c7f2f4ffcc4390acd3e32`.

The partial run recorded three phase invocations. Its only preserved control record is the OFF arm for `dfb-taint-swift-model-opaque-propagator-negative`, observed as `runner-error`; the stop interrupted the run before an ON-arm result. There is no accepted control result, startup summary, 12-arm/36-phase qualification, Unsupported issuance, benchmark attempt, or Joern05 attempt. The separate partial OFF engine diagnosis remains outside this handoff; no semantic engine cause is inferred.

Cleanup sent TERM and the coordinator reaped, with no KILL. All 25 recorded native process births were gone in the root post-stop check, and parent/keepawake births were gone. Descendant containment remains `unknown`; no foreign cleanup is claimed. The ledger remains 109 rows with SHA-256 `2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851`.

## Cause boundary and next gate

The independent stop review is [`native-controls04-stop-independent-review-01.json`](../validation/joern-post-bifrost-01/native-controls04-stop-independent-review-01.json), SHA-256 `211b4a8a30f56e0c23132be52260a643d7ff424630693ac36477323a492be788`. Its pure-Python probe reproduces a split-snapshot ownership race: an owned `swift-frontend` child can be classified as heavy before its exact PID/start identity is merged into the tracked set. The actual offending contender row was not preserved in the terminal/root receipts, so the actual cause identity remains **unknown**. This is a demonstrated repair hypothesis, not a retrospective relabel of the stop.

The review requires a bounded authenticated descendant-start/identity handoff or a single process snapshot carrying PID/start identity/argv, while retaining fail-closed rejection of foreign rows and PID reuse. No command/path exemption, blind retry, sleep, or implementation was performed. Native-controls04’s namespace is consumed and must not be reused.

Addendum11, addendum10, native-controls01–03 failures, the rejected review01, and the publication hold remain preserved. The 18:39 UTC delivery snapshot still needs later supplements; no LFS, upload, repack, source, Git, ledger, runtime-input, analyzer, JVM, engine, admission, or launch mutation was performed for this handoff.

The machine-readable receipt is [`joern-preparation-review-addendum-12.json`](joern-preparation-review-addendum-12.json).

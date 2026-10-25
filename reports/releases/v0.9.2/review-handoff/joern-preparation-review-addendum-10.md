# Joern preparation review addendum 10

Recorded `2026-10-25T19:26:13.975500Z`. This append-only handoff records the actual native-controls03 stop and its independent diagnosis. It preserves the failed namespace and does not approve a qualification, Joern05, engine run, release, or publication.

## Actual stop

The exact request03 was bound to source HEAD `0ad5fcaf482eee32127868a9c3f5f2ce000e9ced`, SHA-256 `ae78aba6c82d1ed10ee59990caa20f5d41b46e7fa29ceafb593f47c486d48fd8`, with 2,287 source refs and 2,240 inherited refs. The independent exact invocation review was `f2fc8aa920988ffb00bfdfed6aa6aa608ef2609c94ff2534f61bcfc62eaf9007` and the fresh admission was `2c24ce7eafd97e21cf16a3825b92e181687496e883e2c98636ec748f17dfceda`; both are retained as inputs to the one attempted launch.

The native-controls03 child reached `ready` and `controls-started`, then stopped at `2026-10-25T19:18:56.702226+00:00` with exit code 1. The frozen runner rejected plan04’s `registered_at_unix_seconds=1792947417.994006` because it is a float while the guard requires an integer. The failure occurred before the version command and before any engine `run_case` loop. The root stop check is `77ac1bf5f493462df05710085e08703618ce4f3913705dc76a5094c103dd2208` and the independent stop review is `4b77f2897ae3eed324e9095b205f8158f31d04814e24b977eafe5d113672ec83`.

The actual Darwin environment repair passed: the child and worker records contain the exact 18-key environment including `__CF_USER_TEXT_ENCODING=0x1F5:0x0:0x0`; the worker environment digest is `ec53d42cc82868a22aba5b88a802c9fa716dc252b6b59cd41e54524d18f3104b`. Parent/worker PIDs existed and are recorded, so these receipts make no JVM-absence claim. The startup sidecar has zero events and no accepted property witness, and no version command completed.

The root check reports all owned PIDs gone: `78659`, `78661`, `80999`, `82812`, and `83571`. The independent review retains descendant containment as unknown, while recording coordinator reaping and no TERM/KILL or foreign cleanup. No benchmark attempt was consumed, no accepted control capture exists, no `run_case` occurred, and no qualification or Unsupported decision was produced.

## Preserved successor work

The plan05 registration handoff is `188c52cbc2743cdce794e60464c01bf37d0369169045677f50a41eeee53d50d8` and its pending plan is `c79f93dca045d8fbf2b7221fbf20e042d7546d403567a821ed1594fda8411137`. It changes only the registration timestamp to integer `1792956319`; it remains `execution_eligible=false`, `fresh_qualification=null`, and `source-candidate-not-qualified`. The private native-qualifier06 candidate and registration-successor design remain pending reviewed successor work. They do not authorize canonical installation, a new request, admission, launch, or qualification. The known 12 unsupported-candidate/control qualification decisions remain missing. Native-controls03 must not be retried or reused.

The prior failed evidence and addendum09 remain preserved. The ledger remains 109 rows and SHA `2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851`. Publication hold remains active.

The machine-readable receipt is [`joern-preparation-review-addendum-10.json`](joern-preparation-review-addendum-10.json).

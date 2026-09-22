# Swift CodeQL activation attempts for #218

These are **non-scored controls**. None is a registry fixture run or score.
Base fixture revision: f3794bb7bb2136d7e1bf8a63a92f2ea3f18620b5.

- Initial recorder stopped during hashing: the system Python lacks
  `hashlib.file_digest`. The already-written environment witnesses remain.
- `attempt-02`: two independent top-level controls compile/link and extract.
  Resolved call declarations exist, but their expressions have no dataflow
  nodes. Both taint queries return empty. This is failed activation, not a clean
  negative. `ActivationNodes.ql` records the zero counts.
- `attempt-03`: fresh controls wrap operations inside `runActivation()` to
  match the registry fixture shape. Positive flow is observed; the retained
  near-miss is empty. A mistaken pack-cache path failed first and is retained.
- `attempt-04`: fresh controls use production module/endpoint identities and
  the production query, including structural Swift.Int and argument checks.
  Positive SARIF contains one flow and both endpoints. Negative SARIF contains
  both endpoints and no flow. The first negative analysis was launched before
  database finalization and failed; the `-02` retry exits successfully but its SARIF retains the earlier error notification. The verifier rejects it; it does not qualify activation.
- `attempt-05`: independent wrong-signature overloads and same-name members;
  zero endpoints and zero flows observed, as required.

The pinned distribution is CodeQL 2.27.0, build
b47b3e59262c95aff4eeb84ac72d09e25a9c37e9. Its exact source tag manifest
`github/codeql@codeql-cli/v2.27.0:swift/ql/lib/qlpack.yml` specifies
`codeql/swift-all@6.8.3`. The resolved transitive lock is retained in
`adapters/codeql/swift/codeql-pack.lock.yml`. Each extraction attempt witnesses
compiler, Xcode, SDK, host, binary hashes, argv, exit status and elapsed time.

Raw BQRS and SARIF, standard output/error, extractor logs, and database metadata
are retained. `.log.txt.gz` preserves logs losslessly despite the repository's `*.log` ignore rule. `compressed-log-manifest.json` binds original and compressed bytes. Complete databases remain in task-owned `/private/tmp/dfb-codeql-swift-218-*`
directories; these are not portable evidence paths. Probe scripts record the
original absolute commands. Timings are descriptive, under host contention.

The first diagnostic query used a nonexistent `Function.getType` API and a
node query had invalid QL syntax; their sources/errors remain under this
folder. These are query-authoring failures, not analyzer scores. The initial
manual diagnostic commands did not retain complete command/timing records;
those partial diagnostics do not certify activation. The production pair's
recorded analyze commands and raw outputs provide the flow activation evidence.

`attempt-06` extracts the near-miss afresh to avoid the retained error; both endpoint observations, zero flow, and no error notifications passed verification.

No modeling activation, scored partition, native profile, extension, real-project
support, or Bifrost Swift support is established by these controls.

`attempt-07-model` retains a failed initial model query and diagnostic corrected
results. `attempt-08-models` combines independently authored load-bearing controls
for source/sink/sanitizer/root/summary/field/key declarations; `attempt-09-receivers`
separates same versus different allocation receivers across procedures.
`attempt-10-calibration` uses a constant-return summary positive and identity-body
no-flow sibling. Intermediate results before corrected curried signatures and
before forced `--rerun` remain diagnostic only.

`final-activation` certifies the initial correct semantic controls;
`final-activation-v2` additionally binds canonical declaration anchors for modeled
source/sink entities and retains sink calls as related locations. The latter is
the certificate source used by the runner. Both are non-scored. The final query
hash manifests and per-command records make reinterpreted/stale results visible.
The strict model verifier checks exact expected model-on/off finding locations,
endpoint observations, fresh evaluation, and absence of error notifications.

SARIF may merge source and sink observation messages at the same location; the
verifiers split exact message lines without treating arbitrary text as identity.
The Rust normalization uses independently validated canonical file/line anchors.

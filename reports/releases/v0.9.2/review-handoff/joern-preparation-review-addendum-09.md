# Joern preparation review addendum 09

Recorded `2026-10-25T19:14:44.001357Z`. This is an append-only source-preparation handoff. It records the exact local source commit and retained evidence; it does not approve native controls, Joern05, engine execution, release, or publication.

## Exact source commit

HEAD is `0ad5fcaf482eee32127868a9c3f5f2ce000e9ced` (`fix: seal native startup environment and execution import order`) with parent `34fdf80bdb6a386af43e3001fc2205c0661560fb` on `dave/v0.9.2-full-refresh`. The commit contains 47 added files and 1,015,642 blob bytes; it was not pushed. The complete binary-safe parent-to-HEAD diff is [`joern-preparation-review-addendum-09-commit-0ad5fcaf-full.diff`](joern-preparation-review-addendum-09-commit-0ad5fcaf-full.diff), 1050543 bytes, SHA-256 `91302bb4030f5a6c46eaa5d92b52ce08a5df925b51ab3c629f3f979e7d1adf95`.

The 47-file change has two source-repair categories. The Python native-control preparation binds the exact Darwin `__CF_USER_TEXT_ENCODING=0x1F5:0x0:0x0` startup field while retaining strict whole-environment equality, unknown-key rejection, and the previously reviewed lifecycle/module cleanup. Its independent source review and canonical-copy review report 48 focused tests. The outer adapter preparation changes packet/import order so the task-owned bridge is verified before the current 95-role graph is composed, while preserving the inherited 88-role graph and rejecting foreign or wrong bridge identities. Its independent source review and canonical-copy review report 72 focused tests.

These are DataFlowBench Python acquisition/adapter and evidence changes. The Bifrost engine is unchanged, the Rust harness was not rebuilt, and no analyzer, replay, admission, launch, or qualification was run. The commit also retains native-controls-02 failure receipts and review metadata; they are historical evidence, not a new attempt.

## Request03 and source proof

The prepared request is [`native-control-request-03.json`](../qualification/joern-post-bifrost-01/native-control-request-03.json), 522,853 bytes, SHA-256 `ae78aba6c82d1ed10ee59990caa20f5d41b46e7fa29ceafb593f47c486d48fd8`, expected HEAD `0ad5fcaf482eee32127868a9c3f5f2ce000e9ced`, namespace `native-controls-03`, and 2,287 source refs (2,240 inherited refs preserved). The committed-source proof is [`native-source-commit-request-check-03.json`](../validation/joern-post-bifrost-01/native-source-commit-request-check-03.json), 923 bytes, SHA-256 `009558b8f1d03f51f28341086b9c9dce39b2bec0211785fd162837a5ccb02d23`. It reports exact committed blobs, the ledger unchanged at SHA `2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851` (109 rows, 123,908,716 bytes), only the ledger dirty, no push, `engine_invoked=false`, and `qualification_invoked=false`. The exact independent invocation review remains pending.

Native-controls-02 remains a failed-before-ready attempt caused by the Homebrew Python startup environment key, with no benchmark attempt consumed, no engine invocation, no qualification, no automatic retry, and no namespace reuse. Native-controls-03 has not been launched. Joern05 has not been launched; no runtime result or Unsupported classification is inferred.

## Historical audit and delivery boundary

The retained full20 case audit remains 1,116 paired case rows against an independent 1,108-case population denominator, with six raw decisive-to-inconclusive transitions and zero raw improvements. Their semantic cause remains unproven. The all20 BF0140 and CodeQL histories were not rerun; only Joern remains missing from the partial matrix boundary.

The historical adapter protocol formatting diagnostic is preserved: `git diff --cached --check` had returned nonzero for one blank line at EOF before the commit. Adapter-04 and adapter-06 protocol bytes were deliberately retained byte-identical (9,505 bytes, SHA-256 `4caf6cd997b75da405b1789ce26cc816dc9244634263f5b000c3de3eed6d49ae`). This is disclosed as a preserved diagnostic, not called a passed check.

Publication hold remains active. No LFS, upload, repack, push, tag, or release action occurred. The root-supplied delivery snapshot boundary is 18:39 UTC on 2026-10-25; this append-only addendum and its diff require a later delivery supplement.

The machine-readable receipt is [`joern-preparation-review-addendum-09.json`](joern-preparation-review-addendum-09.json).

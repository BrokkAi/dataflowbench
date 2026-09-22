# DataFlowBench next-pin discovery handoff

Captured 2026-09-22 23:00:06Z–23:04:43Z UTC from the shared, dirty `dave/swift-release-preparation-220` worktree at `c155aab98da74e4299d8e38404c1342d41783d4b`. The dirty paths are concurrent Swift preparation changes; this metadata audit did not edit repository files. The measured baseline is release `v0.8.0`, freeze revision `80d4f01bb189d530849f9ceb5d775680fcedfb52`.

Proposed integration plan: bump Bifrost `0.11.4 → 0.11.5`, CodeQL CLI `2.27.0 → 2.27.1`, and Joern `4.0.628 → 4.0.633`; hold Semgrep `1.177.0`, OpenTaint semantic/analyzer/rules channels, Infer `v1.3.0`, FlowDroid `v2.15.1`, pyre-check `0.10.0`, and Pyrefly `1.3.1`. The independent Semgrep PyPI check also remains `1.177.0`.

Semgrep Rules requires explicit review: the measured snapshot is `40b8c63f75dc7c22c8a77482d73bfb864b146f7e`; the earlier `311ca4e9ba59d700624539bf658e3d29b134ee77` came from an explicit query of the repository's old `main` branch and is dated 2022-05-11, so it is not the current default branch. The repository metadata identifies `develop` as the default branch; its audited head is `a84ff9cc2453ca91d581380de4b8b3f272f6f4be`, timestamp `2026-09-22T15:34:05Z`, exactly 3 commits ahead and 0 behind the measured snapshot. This manifest does not silently promote that moving head.

OpenTaint remains channel-separated. The semantic release is `v0.4.6`; the analyzer asset channel is immutable `analyzer/2026.09.04.c51dc3e`; product rules are the separate immutable `rules/v0.3.0` release asset `opentaint-rules.tar.gz` at `https://github.com/seqra/opentaint/releases/download/rules/v0.3.0/opentaint-rules.tar.gz`, publisher digest `sha256:3d789c9986479fec792333329abe737eccb15bc06fc59a978a58810118ca1d21`. `analyzer/latest` exists; `rules/latest` and the root `latest` release aliases returned 404, so no alias is treated as a pin.

FlowDroid’s GitHub release has no asset metadata in the current API response. The existing measured Maven jar digest `sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218` is retained as historical evidence only; no artifact was downloaded or runtime-qualified.

CodeQL pack registry endpoints were excluded from this audit. The completed resource-agent record reports 13 current roots, all new for the proposed CodeQL CLI plan, including `codeql/swift-all@6.8.4` and `codeql/swift-queries@1.3.11`; those values are recorded as worker evidence in `SUMMARY.json`, without inventing registry response hashes.

Raw API bodies, response headers, commands, timestamps, HTTP statuses, and SHA-256 digests are in `requests.jsonl`, `commands.log`, `raw/`, and `headers/`. There were 49 metadata requests: 47 HTTP 200 responses and two expected HTTP 404 alias probes. Run `bash verify-audit.sh` in this directory to verify the request count, status counts, every body/header digest, JSON validity, and the target assertions. No packages, binaries, or analyzers were installed or run.

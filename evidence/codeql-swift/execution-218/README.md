# Swift CodeQL execution evidence — #218

All 90 preregistered assertions were attempted once under the committed A35
partition: 66 core, 20 controlled modeling, and 4 calibration. The independent
activation controls are separate under `../activation-218`.

| Tier | Attempted | Inconclusive | Runner error | Qualified reached/not-reached |
| --- | ---: | ---: | ---: | ---: |
| Core | 66 | 12 | 54 | 0 |
| Controlled modeling | 20 | 20 | 0 | 0 |
| Calibration | 4 | 4 | 0 | 0 |

Every native database-create and database-analyze command exited successfully,
without timeout. Every analysis nevertheless measured an individual maximum RSS
above the fixture's unchanged 512 MiB budget: 645–1,664 MiB. CodeQL's minimum heap
adjustments are retained in per-case stderr; `--ram=512` is not a process-tree
limit. Normalized peak memory remains null because aggregate process-tree peak
was not measured. These are budget failures, not successful benchmark coverage.

The 54 core runner errors additionally failed exact endpoint observations. They
retain the memory diagnostic too. The array-element pair is a minimal registry
example of top-level calls yielding no matched dataflow nodes, consistent with
failed non-scored activation attempt-02. Each missing-endpoint row remains an
error; no post-result unsupported partition or blanket causal classification is
substituted. Further extractor/query capability work is required before those
rows can provide valid reachability evidence. No fixture was wrapped or changed.

`summary.json` binds every retained raw file and the three normalized report bytes and details every outcome,
command status, phase time, memory reading and contemporaneous Git HEAD. Run
`python3 evidence/codeql-swift/execution-218/audit.py` from the repository root to
regenerate it. The audit checks all 90 identities exactly once, fixture/compiler/
extractor/pack bytes, configuration equality, and original budget arguments.

The launched runner source was f51cb4c9 (full SHA in summary). Later c7a20bca only
corrected the final report validation sweep. Native execution, normalization and
configuration bytes were unchanged. The originally launched processes repeated
that known sweep failure after successfully writing their reports; unchanged
reports then passed the corrected sweep. `../report-sweep-fix` retains originals,
before/after checks, and byte-equivalence evidence. No execution was relabeled.

At most two sequential CodeQL runners overlapped (core/modeling), each requesting
two threads. Local verification also overlapped. Timings are descriptive and do
not certify the performance track. Problem-kind queries emit no checkpoint path;
empty normalized witness arrays make no witness-track claim.

Opaque/native/extension/real-project deferrals remain as preregistered; Bifrost
Swift remains unsupported. This evidence does not close the resource or endpoint
capability gaps and does not update a release freeze or publish a scored release.

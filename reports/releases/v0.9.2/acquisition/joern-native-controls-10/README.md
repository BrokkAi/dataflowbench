# Joern native controls 10: bounded historical set source preparation

This folder is a source-only follow-up to controls09. It implements the human-approved semantic-only bounded-set rule for ABI4 first-table-only observations while keeping the existing query process, native provider, provider pins, row schema, 5-second limit, 16 MiB query-output bound, and per-observation row bound unchanged.

The evaluator validates the complete first-table-only PID set before calling the descendant-map updater. Any original candidate, pretracked PID, command/other-native PID overlap, duplicate PID, malformed row, incomplete provider result, deadline failure, or capacity failure prevents acceptance of the entire set. If current contender classification finds any contender, the historical set is retained as rejected. Eligible rows are emitted together only after the classifier finds no current contender. The emitted records keep ownership, foreignness, workload relevance, and exact exit time unknown; they cannot enter the current map or argv bridge.

`snapshot_query.py` is byte-identical to controls09. The ABI4 provider source and dylib remain bound to the unchanged controls09 pins recorded in `source-prep-receipt-01.json`.

`test_process_reconciliation_set_policy.py` uses synthetic fixtures only. Its log is `test-log-01.txt`. The source has no query, provider-load, analyzer, native qualification, request admission, eligible-plan, source-CAS, or publication authority. The independent CPU-contention hold remains active.

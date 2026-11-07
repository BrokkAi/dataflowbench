# Joern process-snapshot decision — corrected proposal

The 108 scored cases have **not run**. Qualification06 stopped after startup checks passed because a process disappeared between the native reader's two kernel-table reads. The 130-row ledger is unchanged. The recorded parent, worker and helper PIDs were absent at the root check; descendant containment remains unknown.

The vanished PID differed from the original unresolved candidate; its ownership and workload relevance remain unknown. Table counts do not establish that it was the only difference.

The existing rule rejects the whole native observation for any such disappearance. Merely retaining the vanished row would still fail: the current evaluator also rejects every unbridged kernel-comm row. Proceeding therefore requires an explicit acceptance decision, rather than another retry.

## Proposed narrow change

Use a new, separately reviewed native-provider ABI. Here “first-table-only” means a row within one ABI4 native observation: present in its first kernel table and missing from its second. It does not mean merely present in the outer native-before observation. Preserve the vanished row with its original kernel identity and name as a **historical, unresolved observation**. At most **one** such row may be admitted per already-permitted bounded recheck, across both native observations. Two or more stop the query. This creates no extra recheck or retry; existing phase/run budgets and one-pass-per-original-candidate limits remain in force. A non-candidate row may pass only when it occurred in exactly one native observation, disappeared from that observation's second table, and is absent from the command snapshot and every row of the other native observation. If its PID occurs anywhere in the pre-existing exact tracked map, regardless of birth, the exception is ineligible and the query stops before updating ownership. Historical rows cannot add, remove, replace or downgrade a tracked identity. It cannot establish ownership, join to an argv row, or authorize cleanup. Other current rows may use only the existing exact-identity descendant algorithm. Retain every accepted row in a distinct durable historical-observation collection and use a distinct evaluation status; never call it harmless or unrelated. Keep the existing 8,192-row bound per native observation (16,384 across both); do not increase row, time or resource limits.

An original unresolved candidate appearing anywhere still stops the run. Live contenders, current ambiguous rows, PID reuse, malformed or incomplete provider data, and timeouts still stop it. There is one bounded native–command–native pass within the existing five-second and overall budgets; no new query retry or extra time. Historical ownership, exact exit time and foreignness remain unknown. This does not certify uncontended timing.

The alternative is to keep the strict rule and leave the benchmark blocked. No provider implementation or fresh qualification is authorized by this proposal. After approval, focused positive/near-miss tests, independent review, a fresh source/request binding and admission, and a new qualification namespace are still required. Publication remains held.

Machine-readable proposal: `reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-snapshot-interval-policy-proposal-03.json`.

This corrected proposal preserves proposal01 and the earlier handoff, and addresses independent framing feedback. It remains a proposal awaiting explicit human design approval.

Proposal03 further narrows the exception to one row per existing query and explicitly fails closed on any pre-existing tracked-PID intersection. Proposals01/02 and prior handoffs remain preserved.

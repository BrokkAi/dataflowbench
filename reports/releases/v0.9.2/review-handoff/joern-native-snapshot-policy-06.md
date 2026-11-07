# Joern: bounded historical observations versus strict stop

The108 scored cases have not run. Qualification07 exercised the approved one-row exception once, then stopped on a later recheck with **two** vanished rows. Both individually met the checked absence/exclusion predicates; together they exceeded the approved cap. The run remains failed, its evidence is preserved, and the130-row ledger is unchanged. Historical ownership, workload relevance and exact exit time remain unknown. The cap check returned before the fresh/current-contender classifier ran: the row predicates do **not** establish that this query would have passed under a set policy. Current-contender and current-ambiguity outcomes remain unassessed.

## Explicit design choice

The proposed alternative is a **semantic-only acquisition mode** that checks the same per-PID conditions for every vanished row in the existing bounded observation set, rather than limiting the set to one row. This changes monitor acceptance and does not certify uncontended timings. It must not be described as a passing rerun of qualification07 or used to relax analyzer semantic expectations, timeouts, resource limits or case coverage.

Both native observations stay below8,192 rows each (at most16,384 as the existing combined upper bound), with the same16MiB query-output bound, one existing native–command–native recheck and five-second deadline. There are no extra passes, retries or time. Every row must satisfy the original candidate/tracked exclusions, command/other-native/current absence predicates and exact typed kernel provenance. Any bad row rejects the whole set; no favorable subset may be selected. Live/ambiguous current processes, PID reuse, provider errors, incomplete observations and timeouts still stop.

All accepted rows remain a durable **unresolved historical** collection, never ownership or argv-bridge evidence. Their PIDs enter only a reappearance stop guard. Raw durations may be retained, but earlier competing CPU activity remains unknown: this mode does **not** authorize uncontended-timing certification or relative-performance conclusions. Actual12/36 semantic/startup replay and genuine case evidence remain required before a scored semantic result. Publication still needs the existing full-fix/case-variation/comparability review and subsequent approval.

The alternative is to retain the one-row cap and leave the pinned Joern benchmark blocked. The separately authorized latestJoern test remains separate; no official pin changes follow.

Proposal: `qualification/joern-post-bifrost-01/native-snapshot-set-policy-proposal-02.json`. No implementation, new qualification or scored run is authorized by this document.

# Joern native-control ledger-history successor 08

This namespace contains source and focused synthetic validation for a bounded
ledger-history guard change. It is not an invocation request, native-control
receipt, eligible plan, or scored Joern result.

The wrapper pins the live 130-row ledger digest, the original 109-row byte
prefix, and the exact 21-row Bifrost v0.14.4 suffix. It checks the ordered
global attempts 111 through 131, their attempt IDs, groups and statuses, the
v0.14.4 target identity, and the global completed / failed / recorder-error
counts. The old prefix and all existing observer, plan, core, ABI-3 provider,
environment, process, budget, source-closure and publication-hold rules remain
bound to their prior pins.

`process_reconciliation.py`, `snapshot_query.py`, and `retained_resources.py`
are byte-identical local siblings copied from source 07 for the wrapper's bare
imports and sibling-path checks. `archive_evidence.py` preserves the source 07
implementation byte-for-byte except for `HELPER_SOURCE_PATH`, which is pinned
to this exact 08 copy. Its exact source-path and source-map SHA checks remain
strict. Source 07 remains immutable and is still the authority for its prior
namespace. Provider files and native libraries are not copied into this
source namespace.

The tests exercise only the history validator on synthetic 109+21 row fixtures
and compare source definitions with source 07. They do not import or dispatch a
Joern driver, run a native query, or qualify native controls. A new request,
exact review, and fresh admission remain separate gates after source review and
commit.

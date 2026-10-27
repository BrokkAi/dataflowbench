# Joern native-control source successor 07

This directory is source preparation for the next fresh native-control
qualification. It is not an invocation receipt or an eligible Joern plan.
Native-control execution namespaces 01–05 and their failures remain intact.
The next execution namespace is 06; the source directory number is separate.

The ordinary-user Darwin reader uses SDK `KERN_PROC_ALL` identities instead of
requiring `PROC_PIDTBSDINFO` access to every other process. It retains PID,
parent, birth identity, state, command provenance, and full-table accounting.
Permission/read errors, identity changes, incomplete tables, and current
ambiguity still stop observation. No root access or macOS privacy-setting
change is required by this reader.

`darwin-provider/acquisition-receipt.json` binds the previously compiled ABI3
library and its exact sources. The copied provider README and private handoff
describe their historical source-review stage; the acquisition/build/probe
receipts record the later build and functionality check. After reboot, root
verified all acquisition digests, reran 29 synthetic tests, and made one new
ordinary-user functionality check: 981 full identity rows, six explicit short
command fallbacks, and no permission error. The local postboot receipt is
`execution-state/v092/recovery-20261027/postboot-provider-check.json`, SHA-256
`909f92d8eeccff54de28336d7c67f330237ea8316f61efed5151a97c2b625eca`.
That check does not qualify the monitor or benchmark. A subsequent single full
postboot monitor check passed all three observations (998 native / 999 command /
998 native rows), validated all 22 short-command observations through stable
command bridges, and reaped its own query child with exit 0 and no kill. The
count/hash-only receipt is copied into `monitor-source-recovery-01/`. This is
functionality evidence, not native-control or contender-absence qualification.

The qualifier source and tests were recovered from session-log patches after
the reboot cleared private temporary files. Their hashes and the recovered
historical handoff match the pre-reboot values. A new recovered-source run
passed 57 focused tests. `qualifier-source-recovery-01/` preserves those
historical review documents and the new acquisition receipt. Its compressed
recovery-derived patch is explicitly a new reconstruction, not the unavailable
original historical patch. The old native06 process helper was not copied into
this production candidate. The new monitor source is assembled alongside the
qualifier; the composed suite passed 114 tests with pinned Python 3.13. A further
two-test run strengthened the no-spawn trap without changing production source.
The source review and assembly addendum remain distinct from real controls.

Before invocation, all runtime source must be committed, the new request and
exact invocation independently reviewed, and fresh resource admission passed.
Actual 12-arm/36-phase control results and their review precede an eligible plan
and the remaining 108 scored Joern cases. The 109-row ledger, completed Bifrost
and CodeQL results, original clock, counters, resource floors, one-slot rule,
and pinned tool versions remain unchanged. Publication remains held for David's
review of all fixes and case variation followed by explicit approval.

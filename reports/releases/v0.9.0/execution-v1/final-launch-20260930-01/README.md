# Merged harness launch candidate

This separate prospective packet binds merged PR279 commit `0e42beb655d08081db3123721e1fa7c4b49015e5`. The disabled recovery preparation packet remains immutable. The runner is not built, the recovery allocation is unapproved, no durable claim ledger is initialized, and no exclusive resource slot is reserved.

The prior resource plan remains conservative:192GiB free before the8GiB runner build plus48GiB staging, leaving the unchanged136GiB launch floor. The active Bifrost coverage exporter prevents claiming a slot even when capacity is sufficient. Build only after fresh ownership/process readback, with the registered command and durable supervisor logs; no automatic retry.

After build, bind actual binary/toolchain provenance, perform new Swift query qualification and all117 exact-root runtime/cross-field checks, initialize the reviewed accounting anchor, push the final registration, and submit exact hashes for parent launch review. This packet is not execution approval.

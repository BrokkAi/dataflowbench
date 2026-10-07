# v0.9 resume, 7 October 2026

Prospective preparation descended from the September launch packet. Historical packets, population plans, reports and attempt counts remain unchanged. The user authorized resuming the release and selecting Bifrost v0.12.0. Its public Darwin archive checksum, binary identity and runtime tree are bound here. Fresh adapter/native qualification remains pending.

The missing 1ba0 runtime has been restored under `execution-state/v090-resume-20261007-01`. CodeQL 2.27.1, Swift 6.3.3, patched extractor, all 3,402 pack files and OpenTaint match the immutable historical manifests. The rebuilt extractor has the exact historical binary digest. All twelve relocated Swift queries resolved and compiled with check-only, witnessed by `swift-query-checks/receipt.json`; these checks do not establish corpus results.

The benchmark runner built successfully from unchanged merged Rust source `0e42beb65`; `runner-build.json` binds binary and toolchain provenance. It validates all 1,108 cases and 92 retained reports. The recovery executor uses claim-aware launchers, verifies retained completions, requires all 33 controls before the 84 serial groups, and stops on failures or incompleteness without automatic retry.

Execution remains disabled. Before launch, merge the new executor and v0.12 control, bind their exact merged harness, finalize recovery accounting and durable anchor, and register a fresh exclusive resource reservation. Preserve the 136 GiB launch floor, 40 GiB reserve and single-analyzer policy. Unknown historical claims stay unknown; relocation never resets them. The final reviewed packet must be pushed before dispatch.

All 117 registered control/group argument vectors passed parser-only checks (`command-parsing-check.json`). Full runtime readback remains required immediately before dispatch. The bounded restoration helper also verified the restored candidate trees in place; its default tests do not require local runtime installations.

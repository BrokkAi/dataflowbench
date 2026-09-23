# Isolated Swift toolchain compatibility (#220)

The official Swift 6.3.3 package was acquired from the [Swift.org macOS
installation page](https://www.swift.org/install/macos/), signature-checked as
Swift Open Source (V9AUD2URP3), and verified as trusted by Apple's notary service.
The 1,503,529,808-byte package has SHA-256
`ee82e57774d6650f94aa06302435d6f44a055b9411698db8ecb85d9a3bcc91d0`.
`pkgutil --expand-full` extracted its payload into isolated scratch; no installer
scripts, system Xcode replacement or global toolchain selection were used.

The first version command timed out at 10 seconds without output. A separately
preregistered 60-second retry succeeded and identified Swift 6.3.3. The compiler
then typechecked the retained known String source, environment, argv and exact
static `Process.run` control against the existing macOS 26.5 SDK, with a fresh
module cache and no diagnostics. No fixture binary was executed.

One separately preregistered CodeQL 2.27.1 / swift-all 6.8.4 attempt used this
explicit compiler/SDK/target tuple. Extraction timed out at 60 seconds; no
finalized database or query result was accepted. Its retained extractor log
contains only logging initialization, so the lack of recorded compiler errors
cannot establish complete extractor compatibility. The process timing output
records 692,453,376 bytes maximum RSS, exceeding 512 MiB; this is not a claim
of complete descendant memory accounting. The scored budgets remain unchanged.

The compiler/SDK dependency now has a working isolated typecheck control.
CodeQL extraction/resource qualification remains unresolved. No native role,
unsupported partition, vendor defect or release readiness follows from this
attempt. Any further runtime work needs a new bounded plan; the one-attempt
plan is exhausted. The opaque choice remains pending.

Evidence and preregistrations are under
`evidence/swift-toolchain-compatibility-220/`. Run
`python3 scripts/verify-swift-toolchain-compatibility.py` to verify the retained
hashes and boundaries. Explicit runner overrides require all three of
`--compiler`, `--sdk`, and `--target`, and are restricted to non-scored external
controls. Existing default toolchain selection remains unchanged.

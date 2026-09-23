# Swift Foundation identity diagnostic profile

This is an **adapter-corrected**, non-scored profile for CodeQL CLI 2.27.1 and
`codeql/swift-all` 6.8.4. It intersects the shipped command-injection sinks with
resolved Foundation declaration, owner, signature, and type checks. The vendor
source, barrier, and additional-flow-step definitions remain intact.

- `queries/roles.ql` compares vendor-native and corrected sink roles.
- `queries/flow.ql` compares actual vendor-native and corrected taint flows.
- `queries/signature.ql` exposes the resolved callable/type evidence.
- `../swift-extraction-v2/policy.json` requests prospective analysis at 2048 MiB
  with a 60-second query deadline and a separate 150-second extraction cutoff.

See [the profile contract](../../../docs/swift-foundation-identity-profile.md)
and [retained attempts](../../../evidence/swift-foundation-identity-v1/).
This profile does not supply missing environment/argv sources, activate a
scored corpus, or replace the pinned vendor-native profile. Unresolved identity
fails closed; an empty corrected set alone is not evidence of clean code.

# Bifrost v0.14.4 evidence delivery receipt

Receipt for lossless packaging of the target’s 21 attempt scopes, 19 produced normal-report scopes, and the raw ledger at its 130-row state. Every attempt and normal-report bundle was checked with `scripts/package-v092-evidence.py check`; the ledger archive was restored under the fresh task-owned `/private/tmp` root and matched the canonical ledger byte-for-byte.

The compact scope/hash index is [`benchmark-bundles-01.json`](../../../../../evidence-delivery/v0.9.2-bifrost-v0144-01/benchmark-bundles-01.json). This receipt records storage integrity only, with no benchmark or release qualification.

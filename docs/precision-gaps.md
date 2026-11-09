# Precision-gap templates

Issues [#302](https://github.com/BrokkAi/dataflowbench/issues/302),
[#303](https://github.com/BrokkAi/dataflowbench/issues/303),
[#304](https://github.com/BrokkAi/dataflowbench/issues/304), and
[#305](https://github.com/BrokkAi/dataflowbench/issues/305) add harder siblings
of existing control-flow and container-separation cases. These are prospective
inputs for a future release, likely v0.10.0. They establish fixture semantics,
not analyzer accuracy, qualification, or a published release.

Each applicable template has exactly one positive and one negative per
language, on the `taint` track with `core` tier and `benchmark-controlled`
profile. The source and sink markers, witness checkpoints, provenance, and
negative mechanisms follow the existing case contract. New API variants use
separate identities only when they ask a distinct question; the constant-string
selector remains one semantic identity.

The per-issue contracts record exact identities, language adaptations, and
source-dependence checks:

- [Local constant folding](precision-issue-302.md): conditions become constant
  after folding local bindings, including conditional expressions.
- [Keys in one map](precision-issue-303.md): clean versus tainted keys in one
  local map, with computed-key and callee-escape soundness controls. A positive
  control must contain a real flow, rather than merely request conservative
  treatment of a concretely safe program.
- [Positions after list removal](precision-issue-304.md): removing the first
  element shifts the tainted value to index zero; reading the new index one is
  safe.
- [Constant string selector](precision-issue-305.md): a standard string
  operation drives switch/when/match selection. This is primarily a benchmark
  idiom, kept to one template.

| Language scope | Added core pairs | Added assertions |
| --- | ---: | ---: |
| C | 4 | 8 |
| Go | 6 | 12 |
| Each of the other 12 languages | 7 | 14 |
| Total | 94 | 188 |

C has no standard associative map counterpart for the three map identities.
Go has no conditional expression counterpart for the second folding identity.
The per-issue contracts explain these language boundaries without changing any
other language's denominator.

Semgrep CE keeps its existing preregistered local/heap boundary. The two folding
identities and the string-selector identity join its `intraprocedural` scored
partition: six additional assertions per language, or four in Go. Map and list
identities remain outside that bounded heap/index profile under the existing
`heap-access-path` classification. These prospective decisions precede analyzer
execution; historical reports and their partitions are unchanged.

## Registration and historical boundaries

The exact prospective additions are listed in
[`populations/precision-gaps-v1.json`](../populations/precision-gaps-v1.json).
The registry binds each case and fixture by SHA-256 and explicitly records each
template's applicable languages. `cargo run -- validate` verifies complete
balanced registration and adds those identities to moving main's core
denominators. A missing pair, duplicate, changed byte, or unregistered core
fixture fails validation.

`python3 scripts/refresh-precision-inventory.py` checks the inventory against
the explicit seven-template applicability table. After reviewing a prospective
fixture edit, `--write` refreshes only those registered paths and digests; it
never scans for or admits unrelated fixtures.

The inventory is a prospective input registration, not a `freeze/v1` manifest.
Existing named populations and released manifests retain their exact members,
bytes, budgets, analyzer pins and results. Historical Swift file-closure checks
exclude only the exact registered new paths with verified bytes. Unknown paths
still fail closure; changing a registered file cannot hide it from validation.
Historical coverage audits continue to describe their original populations.
The Bifrost smoke selector also excludes these registered identities explicitly,
preserving its historical 118-case population even when a new fixture names an
existing smoke policy.

The two hash-bound Swift validator/adapter source inputs changed by this work
retain exact [predecessor snapshots](../adapters/precision-predecessor-v1/README.md).
Legacy reports may match only their original logical-path hash, with every
other closure input still verified. The validator reports this as a historical
match and names the source revision; it does not rewrite a stamped hash, extend
a qualification, or add a stale-report exception.

Runtime fixture controls and analyzer evidence remain distinct. Executing a
positive with two source values checks concrete dependence; a safe negative
must remain independent under the construction's language semantics. A missing
toolchain is an unperformed check, and an incomplete analyzer result remains
incomplete. No new scores or support claims follow from these additions.

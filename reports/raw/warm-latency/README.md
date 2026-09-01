# Warm-marginal latency artifacts

Auxiliary timing evidence for the latency tier's warm-marginal figures. These
are **outside the freeze**: `freeze/v1` binds normalized reports and one
raw-evidence digest per result, and does not digest anything here. Nothing in
this directory is read by the scoring path, by `validate-reports`, or by the
freeze manifest.

Two amendments have written into this directory, and both records are kept.

## Live — [Amendment A21](../../../docs/latency-tier.md#amendments)

Published figures are **ranges over retained repeats**, and these are the files
the site derives them from:

| Path | What it is |
| --- | --- |
| `joern-java-kernel/warm-latency.json` | Joern, Java kernel: two retained repeats, published as the range their slopes span. |
| `joern-java-kernel/run-<n>-batch-<k>-evidence/` | The per-case evidence each batch of each repeat produced, so a reader can check the batch did the real work rather than less of it. |
| `semgrep-java-kernel/warm-latency.json` | Semgrep CE, Java kernel: two retained repeats, published as a range. A21 reverses A15's withhold of this figure. |
| `semgrep-java-kernel/run-<n>-batch-<k>-findings.json` | The verbatim `--json` document each batch produced. |
| `*/run-environment.json` | The environment stamp each measurement ran under. |

## Superseded — [Amendment A15](../../../docs/latency-tier.md#amendments)

A15's figures are **retired, not deleted**. They are what the project published,
and the record of a retired number belongs beside the number that replaced it:

| Path | What it is |
| --- | --- |
| `superseded-a15/joern-java-kernel/warm-latency.json` | A15's published Joern figure — a **single** run, giving the point estimates 1.55 s (least squares) and 1.54 s (endpoint). Superseded by the range in the live artifact. Byte-identical to what A15 published; nothing in it was edited. |
| `superseded-a15/joern-java-kernel/batch-<k>-evidence/` | The per-case evidence behind that single run. Retained on the same principle. |
| `semgrep-java-stability-probe/` | The two Semgrep runs A15 cited as its reason to **withhold** a Semgrep figure. A15 names this path, so it stays exactly where A15 put it. A21 reverses the withhold: see that directory's own README for why the two runs disagreed. |

**Why the retired figures sit in their own tree.** The warm runner clears its
output directory at the start of every run, which is correct for its own
outputs — a stale batch from a previous run must never be read as part of a new
one — and fatal for retired evidence parked beside them. `superseded-a15/` is a
tree the runner never writes to. This was learned the direct way: an earlier
arrangement kept A15's artifact inside `joern-java-kernel/`, and the next
re-measurement deleted it.

One stamp inside the retired artifact is stale and is left that way: its
`"amendment"` field reads `"A13"`, the number this amendment carried before the
A13/A14 race renumbered it to A15. `fb4f1141` renumbered the prose but not the
field. It is a verbatim copy of published evidence, so it is not edited here —
the live artifacts carry `"amendment": "A21"` and `"establishing_amendment":
"A15"`.

**Why they were superseded, in one line:** A15's publication rule gated on two
repeats "agreeing closely" without naming a tolerance, and its measurements were
taken on a busier machine (its own artifacts record load 9.1–9.5, against
2.0–3.9 for the live figures). A21 replaces the rule with a range over retained
repeats — which needs no tolerance — and re-measures on an idle machine. The
full account is in A21.

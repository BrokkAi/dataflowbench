# Semgrep warm-marginal stability probe — the evidence behind a decline

Amendment A13's observability audit found that Semgrep CE **does** expose a
real multi-case batch in its released CLI: one `semgrep scan` accepts many
target paths. So the batch was implemented and measured, on the largest
identical-rule group of the Java kernel's invocable assertions.

It is **not published**, and this directory is why.

`semgrep scan` carries one `--config`, so a batch is the same work as its *k*
cold runs only when all *k* cases resolve to identical rule text. That caps
*k* at 12 here — and every Semgrep kernel in this benchmark invokes exactly 14
cases, the rest being declared-capability `unsupported` decided before
invocation, so no other language would raise the ceiling either. At *k* ≤ 12
the whole batch takes two to three seconds, of which the per-case work is a
small part, and the slope is not large against the machine's own noise.

The same measurement was therefore run twice, back to back, under the same
conditions. The two runs are retained here verbatim:

| Run | Batch series (`k` → ms) | Endpoint slope | Least-squares slope |
| --- | --- | --- | --- |
| `probe-run-1.json` | 1→2376, 2→1999, 4→2792, 8→2677, 12→3209 | 75.7 ms | 83.9 ms |
| `probe-run-2.json` | 1→1787, 2→1854, 4→2257, 8→3092, 12→3457 | 151.6 ms | 163.4 ms |

The two slopes differ by roughly a **factor of two**, and run 1's series is not
even monotone in *k*. A figure that unstable is not one this tier should
publish beside numbers that are stated to two significant figures, so no
Semgrep warm marginal appears on the latency page and the observability table
records the decline with this probe as its evidence.

What *does* survive both runs, and is the only thing said about it anywhere:
both slopes are about an order of magnitude below Semgrep's cold median. That
is a statement about the shape of the cost, not a number, and it is not
published as one.

This directory holds no `warm-latency.json`, which is how the site's build-time
derivation knows not to read it: it publishes only directories that carry that
file. These are auxiliary probe artifacts, outside the freeze, exactly as the
published warm artifacts are.

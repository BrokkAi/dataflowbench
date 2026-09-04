/**
 * Immutable cold-latency corpus selected by each snapshot page.
 *
 * This is intentionally separate from the `current` flag and from the current
 * correctness results. A correctness-only freeze may reuse an earlier latency
 * corpus, as v0.6.1 and v0.7.0 both do, without relabelling or expanding it.
 *
 * Two freezes therefore now render the same v0.6.0 corpus, and neither of them
 * re-measured it: v0.7.0's re-pins moved Bifrost, Semgrep CE, Joern and
 * OpenTaint, and none of those movements reaches a timing here.
 */
export const LATENCY_EVIDENCE_RELEASE_BY_SNAPSHOT: Readonly<
  Record<string, string>
> = {
  'v0.6.0': 'v0.6.0',
  'v0.6.1': 'v0.6.0',
  'v0.7.0': 'v0.6.0',
};

export function latencyEvidenceRelease(snapshotVersion: string): string {
  const release = LATENCY_EVIDENCE_RELEASE_BY_SNAPSHOT[snapshotVersion];
  if (!release) throw new Error(`${snapshotVersion} has no latency corpus`);
  return release;
}

/**
 * Immutable cold-latency corpus selected by each snapshot page.
 *
 * This is intentionally separate from the `current` flag and from the current
 * correctness results. A correctness-only freeze may reuse an earlier latency
 * corpus, as v0.6.1 does, without relabelling or expanding it.
 */
export const LATENCY_EVIDENCE_RELEASE_BY_SNAPSHOT: Readonly<
  Record<string, string>
> = {
  'v0.6.0': 'v0.6.0',
  'v0.6.1': 'v0.6.0',
};

export function latencyEvidenceRelease(snapshotVersion: string): string {
  const release = LATENCY_EVIDENCE_RELEASE_BY_SNAPSHOT[snapshotVersion];
  if (!release) throw new Error(`${snapshotVersion} has no latency corpus`);
  return release;
}

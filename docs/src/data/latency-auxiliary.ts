import v071Evidence from './archive/v0-7-1-latency-auxiliary-evidence.json';
import { boundEvidence } from './evidence-binding';
import v060AuxiliaryEvidence from './archive/v0-6-0-latency-auxiliary-evidence.json';
import type { Snapshot } from './snapshots';

export const V060_AUXILIARY_EVIDENCE_REF =
  'ccbcd788aabec2abe60200573f38bc42128d00f0';

interface AuxiliaryEvidence {
  schema_version: number;
  evidence_ref: string;
  latency_release: string;
  artifacts: Record<string, any>;
}

const evidenceByRelease: Record<
  string,
  { evidenceRef: string; evidence: AuxiliaryEvidence }
> = {
  'v0.7.1': {
    evidenceRef: '2007f15d687e0081c948e55bba39c952d248ee0f',
    evidence: v071Evidence as AuxiliaryEvidence,
  },
  'v0.6.0': {
    evidenceRef: V060_AUXILIARY_EVIDENCE_REF,
    evidence: v060AuxiliaryEvidence as AuxiliaryEvidence,
  },
};

/** Immutable amendment evidence associated with a snapshot's cold corpus. */
export function auxiliaryLatencyEvidence(
  snapshot: Snapshot,
): AuxiliaryEvidence {
  const release = snapshot.latencyEvidenceRelease;
  if (!release) throw new Error(`${snapshot.version} has no latency corpus`);
  return boundEvidence(release, evidenceByRelease, (evidence) => ({
    release: evidence.latency_release,
    revision: evidence.evidence_ref,
    schema: evidence.schema_version,
  }));
}

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

const evidenceByRelease: Record<string, AuxiliaryEvidence> = {
  'v0.6.0': v060AuxiliaryEvidence as AuxiliaryEvidence,
};

/** Immutable amendment evidence associated with a snapshot's cold corpus. */
export function auxiliaryLatencyEvidence(
  snapshot: Snapshot,
): AuxiliaryEvidence {
  const release = snapshot.latencyEvidenceRelease;
  if (!release) throw new Error(`${snapshot.version} has no latency corpus`);
  const evidence = evidenceByRelease[release];
  if (!evidence)
    throw new Error(`${release} has no auxiliary latency evidence`);
  if (
    evidence.schema_version !== 1 ||
    evidence.latency_release !== release ||
    evidence.evidence_ref !== V060_AUXILIARY_EVIDENCE_REF
  ) {
    throw new Error(
      `${release}: auxiliary latency evidence is not the pinned bundle`,
    );
  }
  return evidence;
}

/** Fail closed when a snapshot has no explicitly registered immutable evidence. */
export function boundEvidence<T>(
  release: string,
  registry: Readonly<Record<string, { evidenceRef: string; evidence: T }>>,
  identity: (evidence: T) => { release: string; revision: string; schema: number },
): T {
  const entry = registry[release];
  if (!entry) throw new Error(`${release} has no registered evidence`);
  const actual = identity(entry.evidence);
  if (
    !/^[0-9a-f]{40}$/.test(entry.evidenceRef) ||
    actual.schema !== 1 ||
    actual.release !== release ||
    actual.revision !== entry.evidenceRef
  ) {
    throw new Error(`${release}: evidence does not match its immutable binding`);
  }
  return entry.evidence;
}

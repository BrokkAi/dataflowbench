# Swift fixture compilation evidence

These records validate fixture construction only. They are not analyzer results,
activation probes, scored evidence, or a release freeze.

- `20260922-attempt1`: failed before fixture compilation because the
  initial identity reader looked for the driver banner only on stdout; this
  compiler writes it on stderr. Retained unchanged.
- `20260922-attempt2`: witnessed the exact pin; compiled 26 cases before
  Swift rejected the exception fixture's non-exhaustive catch. Retained unchanged.
- `20260922-attempt3`: all 90 cases compiled and linked; all 68 concrete
  controls passed with inputs 7 and 19. The 20 modeling cases and two modeled
  summary calibration cases are compile/link-only. No abstract model claim.

The tracked files are explicitly path-redacted exports of unchanged local raw
records. `scripts/export-swift-evidence.py` replaces worktree/home/temp roots
with placeholders and withholds the personal PATH value, recording the original
raw SHA-256. Original `local-*` directories remain locally retained and ignored.

Every export retains command structure, selected environment, output, exit statuses, exact
compiler/SDK identity, and digests. The successful attempt binds current case
and source bytes and validator script digest; its uncommitted-worktree origin
is not a claim that the then-current Git HEAD contained those bytes. Bounded
runtime controls establish the observed dependence/independence for the two
inputs, not an analyzer proof or exhaustive execution proof.

The automatic PR CI job retains a separate hosted-profile artifact associated
with its actual workflow SHA and run identity. See the prospective A34 in
`docs/swift-kernel.md` for the rolling-host boundary. Historical freezes and
failed attempts are not rewritten.

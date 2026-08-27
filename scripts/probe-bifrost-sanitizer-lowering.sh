#!/usr/bin/env bash
# Amendment A9's evidence: Bifrost's category Z, measured rather than assumed.
#
# The preregistration declined category Z for Bifrost on a sentence in the
# adapter README — "Sanitizer lowering is a future Bifrost CLI capability." This
# probe is what withdrew it. It is the same shape as the two per-language
# load-bearing probes beside it (docs/modeling-matrix.md#the-load-bearing-model-requirement):
# each fixture is run twice, once against the committed modeling policy and once
# against a copy with the `:sanitizers` section deleted, and both raw outputs are
# retained. What it adds is the third direction a sanitizer needs, which no
# other category does:
#
#   1. **Suppression.** Template 5's negative — the flow routed through the
#      declared `scrub` — reports nothing, on a run that *completes*. A
#      suppression that came from an incomplete analysis would be vacuous, so
#      the retained report's `completion` is part of the evidence.
#   2. **Restoration.** The same fixture with the declaration removed reports
#      the flow again, with a complete witness. This is what makes the
#      declaration load-bearing rather than decorative: without it, the cell is
#      decided by the engine, not by the model.
#   3. **Selectivity.** Template 6's positive routes the flow through the
#      *undeclared* `sanitize` — same shape, same identity body, a name at
#      least as sanitizer-shaped — and is still reported. A sanitizer bound by
#      name shape rather than by declared identity would suppress it.
#
# Template 5's positive is retained alongside as the non-vacuity control: the
# flow exists at all, so the negative's absence means something.
#
# The probe never touches a committed artifact, never writes a report, and never
# feeds a normalized outcome.
#
# Usage:
#   scripts/probe-bifrost-sanitizer-lowering.sh --bifrost <path>
set -euo pipefail

BIFROST=bifrost
while [ $# -gt 0 ]; do
  case "$1" in
    --bifrost) BIFROST="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a9-bifrost-sanitizer"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

# The counterfactual policy: the committed artifact with its `:sanitizers`
# section removed and nothing else changed. The section is cut between its own
# key and the `:sinks` key that follows it, so the surrounding policy stays
# parseable — an unparseable counterfactual would be a probe failure rather
# than a measurement.
strip_sanitizers() { # <committed policy> <counterfactual policy>
  python3 - "$1" "$2" <<'PY'
import sys
source, destination = sys.argv[1], sys.argv[2]
text = open(source).read()
start = text.index("    :sanitizers (endpoint-set :entries [")
end = text.index("    :sinks (endpoint-set")
if start >= end:
    raise SystemExit("the sanitizer section is not where the probe expects it")
open(destination, "w").write(text[:start] + text[end:])
PY
}

probe() { # <language> <fixture extension> <case suffix> <with|without> <policy>
  local language="$1" extension="$2" case_id="$3" variant="$4" policy="$5"
  local workspace="$SCRATCH/$language-$case_id-$variant"
  rm -rf "$workspace"
  mkdir -p "$workspace"
  cp "$ROOT/cases/taint/$language/model-sanitizer-$case_id"/*."$extension" "$workspace/"
  cp "$policy" "$workspace/policy.rqlp"
  "$BIFROST" --root "$workspace" --policy-file policy.rqlp \
    --evaluation-date 2026-08-11 --format json --fail-on never \
    --output "$OUT/$language-sanitizer-$case_id-$variant-model.json" || true
}

for language in python javascript java; do
  case "$language" in
    python) extension=py ;;
    javascript) extension=js ;;
    java) extension=java ;;
  esac
  committed="$ROOT/adapters/bifrost/policies/model-$language.rqlp"
  strip_sanitizers "$committed" "$SCRATCH/$language-without.rqlp"

  # 1. Suppression, and the control that keeps it from being vacuous.
  probe "$language" "$extension" kill-positive with "$committed"
  probe "$language" "$extension" kill-negative with "$committed"
  # 2. Restoration: the same negative with the declaration deleted.
  probe "$language" "$extension" kill-negative without "$SCRATCH/$language-without.rqlp"
  # 3. Selectivity, in both of its directions: the undeclared sanitizer-shaped
  #    call does not suppress, and the declared one does.
  probe "$language" "$extension" selectivity-positive with "$committed"
  probe "$language" "$extension" selectivity-negative with "$committed"
done

echo "retained Amendment A9 probe evidence under reports/raw/amendment-a9-bifrost-sanitizer/"

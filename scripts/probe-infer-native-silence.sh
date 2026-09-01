#!/usr/bin/env bash
# Amendment A14's evidence: Infer's tool-native row declines on a MEASURED
# silence, not a swallowed misconfiguration.
#
# The pinned v1.3.0 ships Pulse's taint analysis disabled absent a
# `--pulse-taint-config`, and the one silent-failure mode the kernel adapter
# guards — a mis-pathed configuration is silently ignored, exit zero, empty
# report — would make an asserted decline indistinguishable from a swallowed
# mistake. This probe removes that ambiguity by construction: it passes **no**
# configuration argument at all, so there is nothing to mis-path, and it
# retains the exact argv beside every verbatim SARIF. Each of the twelve Java
# tool-native fixtures is captured and analyzed by the shipped product as
# shipped (`analyze --pulse-only --sarif`, nothing else), and the retained
# outcome is what the product decided on its own: zero findings of any rule.
#
# The always-enabled Simple→Simple policy is retained from the binary's own
# help text alongside, because it is the one shipped activation that exists —
# and with no shipped Java source or sink bound to the Simple kinds, it
# decides nothing.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome.
#
# Usage:
#   scripts/probe-infer-native-silence.sh --infer <path> [--javac <path>]
set -euo pipefail

INFER=infer
JAVAC=javac
while [ $# -gt 0 ]; do
  case "$1" in
    --infer) INFER="$2"; shift 2 ;;
    --javac) JAVAC="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a14-infer-native-silence"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

"$INFER" --version | head -1 > "$OUT/witnessed-version.txt"

# The shipped default policy, from the binary's own help text: Simple→Simple
# is always enabled, and nothing in the shipped product binds a Java source or
# sink to the Simple kinds.
"$INFER" analyze --help 2>&1 \
  | sed -n '/--pulse-taint-policies json/,/--pulse-taint-propagators/p' \
  > "$OUT/always-enabled-policy-help.txt"

for case_dir in "$ROOT"/cases/taint/java/native-*; do
  case="$(basename "$case_dir")"
  work="$SCRATCH/$case"
  mkdir -p "$work/dataflowbench/taint"
  cp "$case_dir"/*.java "$work/dataflowbench/taint/"
  (
    cd "$work"
    "$INFER" capture --results-dir infer-out -- \
      "$JAVAC" dataflowbench/taint/*.java > capture.log 2>&1
    "$INFER" analyze --results-dir infer-out --pulse-only --sarif \
      > analyze.log 2>&1
  )
  analyze_status=$?
  cp "$work/infer-out/report.sarif" "$OUT/$case.sarif.json"
  python3 - "$case" "$OUT" "$work/infer-out/report.sarif" "$analyze_status" <<'PY'
import json, sys
case, out, sarif_path, status = sys.argv[1:5]
sarif = json.load(open(sarif_path))
results = [r for run in sarif.get("runs", []) for r in run.get("results", [])]
summary = {
    "probe": case,
    "invocation": [
        "analyze", "--results-dir", "infer-out", "--pulse-only", "--sarif"
    ],
    "pulse_taint_config_argument": None,
    "analyze_exit_status": int(status),
    "result_count": len(results),
    "rule_ids": sorted({r.get("ruleId") for r in results}),
    "evidence_kind": "retained-native-silence-probe",
}
with open(f"{out}/{case}.json", "w") as fh:
    json.dump(summary, fh, indent=2)
    fh.write("\n")
print(f"{case}: results={len(results)}")
PY
done

echo "retained native-silence evidence under reports/raw/amendment-a14-infer-native-silence/"

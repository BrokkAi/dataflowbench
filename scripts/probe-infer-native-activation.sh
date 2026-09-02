#!/usr/bin/env bash
# Amendment A28's evidence: Infer's tool-native decline is re-grounded on an
# enumerated-and-executed activation surface, not only on A14's measured
# silence.
#
# A14 established that the shipped product, invoked with no
# `--pulse-taint-config` at all, produces zero findings over the twelve Java
# native fixtures. It described that silence as "Pulse taint is off absent a
# configuration". This probe interrogates the half of the question A14 never
# executed: whether the pinned distribution BUNDLES default taint data that a
# zero-configuration invocation activates, and whether the full default
# checker surface (`infer run`, not the adapter's `--pulse-only` arm) decides
# anything the split invocation missed. Three arms, all executed against the
# pinned binary:
#
# 1. **Enumeration** — every file under the distribution's config tree is
#    retained verbatim with its digest and its top-level JSON keys, and the
#    whole distribution is searched for `.inferconfig` and for any other
#    taint-named artifact. The result: one bundled directory,
#    `lib/infer/infer/config/taint/`, whose own README states the configs
#    "are always included when running infer" — four Objective-C NSLib files
#    declaring `pulse-taint-propagators` ONLY. No source, no sink, no
#    sanitizer, no policy, no Java identity, anywhere in the shipped tree.
#
# 2. **Engagement proof** — the loader is proven live rather than assumed:
#    the distribution is copied byte-for-byte to scratch, one bundled config
#    is corrupted in the copy, and a zero-configuration invocation on a Java
#    fixture dies (exit 3) naming the corrupted file from
#    `Config.pulse_taint_config`'s directory fold. The bundle is therefore
#    parsed unconditionally on every invocation — the silence A14 measured is
#    an ENGAGED silence: the machinery loads the shipped taint data and that
#    data binds no endpoint to any policy.
#
# 3. **Full default surface** — `infer run --sarif` (capture + analyze with
#    the release's default checker set, nothing disabled) over all twelve
#    Java native fixtures, verbatim SARIF retained per fixture. Zero findings
#    of any rule, taint-shaped or otherwise: no non-taint default checker
#    fires anywhere, so there is no away-from-anchor diagnostic to reconcile
#    and no live flow question deciding not-reached.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome. The pinned distribution is never
# modified: the corruption arm operates on a scratch copy that is removed on
# exit.
#
# Usage:
#   scripts/probe-infer-native-activation.sh --infer <path> [--javac <path>]
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
OUT="$ROOT/reports/raw/amendment-a28-infer-native-activation"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

"$INFER" --version | head -1 > "$OUT/witnessed-version.txt"

# Resolve the distribution root from the invoked binary: the loader resolves
# its bundled config tree relative to the real binary
# (lib/infer/infer/bin/../config), so the distribution root is three levels
# above the resolved binary.
REAL_BIN="$(python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$(command -v "$INFER")")"
DIST_ROOT="$(cd "$(dirname "$REAL_BIN")/../../../.." && pwd)"
CONFIG_DIR="$(dirname "$REAL_BIN")/../config"

# --- Arm 1: enumeration -----------------------------------------------------
mkdir -p "$OUT/shipped-taint-bundle"
(cd "$CONFIG_DIR" && find . -type f | sort) | while read -r rel; do
  mkdir -p "$OUT/shipped-taint-bundle/$(dirname "$rel")"
  cp "$CONFIG_DIR/$rel" "$OUT/shipped-taint-bundle/$rel"
done
python3 - "$DIST_ROOT" "$CONFIG_DIR" "$OUT" <<'PY'
import hashlib, json, os, sys
dist_root, config_dir, out = sys.argv[1:4]
entries = []
for dirpath, _, files in sorted(os.walk(config_dir)):
    for name in sorted(files):
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, config_dir)
        entry = {
            "path": rel,
            "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
        }
        if name.endswith(".json"):
            entry["top_level_keys"] = sorted(json.load(open(path)))
        entries.append(entry)
inferconfigs = []
other_taint = []
for dirpath, _, files in os.walk(dist_root):
    for name in files:
        rel = os.path.relpath(os.path.join(dirpath, name), dist_root)
        if name == ".inferconfig" or name.startswith("inferconfig"):
            inferconfigs.append(rel)
        elif "taint" in name.lower() and not rel.startswith(
            os.path.relpath(config_dir, dist_root).replace("bin/..", "")
        ) and "config/taint" not in rel:
            other_taint.append(rel)
manifest = {
    "probe": "shipped-taint-bundle-enumeration",
    "distribution_root": dist_root,
    "config_tree_files": entries,
    "dot_inferconfig_files_in_distribution": sorted(inferconfigs),
    "taint_named_files_outside_config_tree": sorted(other_taint),
    "evidence_kind": "retained-native-activation-probe",
}
with open(f"{out}/shipped-taint-bundle-manifest.json", "w") as fh:
    json.dump(manifest, fh, indent=2)
    fh.write("\n")
print("bundle files:", len(entries), "| .inferconfig:", len(inferconfigs))
PY

# --- Arm 2: engagement proof ------------------------------------------------
cp -R "$DIST_ROOT" "$SCRATCH/dist-copy"
COPY_BIN="$SCRATCH/dist-copy/bin/infer"
COPY_TARGET="$SCRATCH/dist-copy/lib/infer/infer/config/taint/objc/NSLib/NSString_taintconfig.json"
echo '{ this is not json' > "$COPY_TARGET"
work="$SCRATCH/engagement"
mkdir -p "$work/dataflowbench/taint"
cp "$ROOT"/cases/taint/java/native-source-sink-positive/*.java \
  "$work/dataflowbench/taint/"
set +e
(
  cd "$work"
  "$COPY_BIN" capture --results-dir infer-out -- \
    "$JAVAC" dataflowbench/taint/*.java
) > "$OUT/engagement-proof-transcript.txt" 2>&1
engagement_status=$?
set -e
python3 - "$OUT" "$engagement_status" <<'PY'
import json, sys
out, status = sys.argv[1:3]
transcript = open(f"{out}/engagement-proof-transcript.txt").read()
summary = {
    "probe": "zero-config-engagement-proof",
    "mechanism": (
        "byte copy of the pinned distribution; one bundled config file "
        "corrupted in the copy; zero-configuration capture of a Java fixture"
    ),
    "corrupted_file": "lib/infer/infer/config/taint/objc/NSLib/NSString_taintconfig.json",
    "pulse_taint_config_argument": None,
    "exit_status": int(status),
    "died_on_corrupted_bundle": "Could not read or parse Infer Pulse JSON config"
    in transcript,
    "loader_frame_named": "IBase__Config.pulse_taint_config" in transcript,
    "evidence_kind": "retained-native-activation-probe",
}
assert summary["exit_status"] != 0, "corrupted bundle was silently ignored"
assert summary["died_on_corrupted_bundle"], "parse error not surfaced"
with open(f"{out}/engagement-proof.json", "w") as fh:
    json.dump(summary, fh, indent=2)
    fh.write("\n")
print(f"engagement proof: exit={status}, bundle parsed unconditionally")
PY

# --- Arm 3: full default surface --------------------------------------------
for case_dir in "$ROOT"/cases/taint/java/native-*; do
  case="$(basename "$case_dir")"
  work="$SCRATCH/$case"
  mkdir -p "$work/dataflowbench/taint"
  cp "$case_dir"/*.java "$work/dataflowbench/taint/"
  (
    cd "$work"
    "$INFER" run --results-dir infer-out --sarif -- \
      "$JAVAC" dataflowbench/taint/*.java > run.log 2>&1
  )
  run_status=$?
  cp "$work/infer-out/report.sarif" "$OUT/$case-full-default.sarif.json"
  python3 - "$case" "$OUT" "$work/infer-out/report.sarif" "$run_status" <<'PY'
import json, sys
case, out, sarif_path, status = sys.argv[1:5]
sarif = json.load(open(sarif_path))
results = [r for run in sarif.get("runs", []) for r in run.get("results", [])]
summary = {
    "probe": case,
    "invocation": ["run", "--results-dir", "infer-out", "--sarif"],
    "checker_selection": "release default set (no --pulse-only, nothing disabled)",
    "pulse_taint_config_argument": None,
    "run_exit_status": int(status),
    "result_count": len(results),
    "rule_ids": sorted({r.get("ruleId") for r in results}),
    "evidence_kind": "retained-native-activation-probe",
}
with open(f"{out}/{case}-full-default.json", "w") as fh:
    json.dump(summary, fh, indent=2)
    fh.write("\n")
print(f"{case}: full-default results={len(results)}")
PY
done

echo "retained native-activation evidence under reports/raw/amendment-a28-infer-native-activation/"

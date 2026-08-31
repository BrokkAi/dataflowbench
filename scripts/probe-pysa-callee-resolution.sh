#!/bin/sh
# Isolate the pinned pyre-check/Pyrefly pair's higher-order callee boundary
# on the dispatch-table shape: the pair resolves every direct call in the
# fixture — dfb_source, leak, drop, even dict.__getitem__ — and exports the
# dispatching call `table[key](...)` itself as an unresolved
# `UnexpectedCalleeExpression`, so the taint fixpoint has no edge to carry
# the flow over. The retained evidence under
# reports/raw/pysa-callee-resolution-probe/ is this probe's output: the
# call-graph entries for dispatch_table.run and the taint evidence showing
# both endpoint models bound and zero issues.
#
# Usage:
#   scripts/probe-pysa-callee-resolution.sh \
#     --pyre /path/to/pyre --pyre-binary /path/to/pyre.bin \
#     --pyrefly /path/to/pyrefly
#
# The probe is evidence, not a partition input: the scored population is
# unchanged by it.
set -eu

PYRE="" PYRE_BINARY="" PYREFLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --pyre) PYRE="$2"; shift 2 ;;
    --pyre-binary) PYRE_BINARY="$2"; shift 2 ;;
    --pyrefly) PYREFLY="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$PYRE" ] && [ -n "$PYRE_BINARY" ] && [ -n "$PYREFLY" ] || {
  echo "usage: $0 --pyre PYRE --pyre-binary PYRE_BIN --pyrefly PYREFLY" >&2
  exit 2
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$ROOT/reports/raw/pysa-callee-resolution-probe"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/dataflowbench-pysa-probe.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

mkdir -p "$WORK/src" "$WORK/models"
cp "$ROOT/cases/taint/python/dispatch-table-positive/dispatch_table.py" "$WORK/src/"
cp "$ROOT/adapters/pysa/taint.config" "$WORK/models/taint.config"
sed \
  -e 's/__DFB_SOURCE_MODULE__/dispatch_table/' \
  -e 's/__DFB_SINK_MODULE__/dispatch_table/' \
  -e 's/__DFB_SOURCE__/dfb_source/' \
  -e 's/__DFB_SINK__/dfb_sink/' \
  "$ROOT/adapters/pysa/models/kernel-python.pysa" > "$WORK/models/dfb.pysa"
printf 'project-includes = ["src/**/*.py"]\n' > "$WORK/pyrefly.toml"
printf '{"source_directories": ["src"], "taint_models_path": ["models"]}\n' \
  > "$WORK/.pyre_configuration"

( cd "$WORK" && \
  PATH="$(dirname "$PYREFLY"):$PATH" \
  "$PYRE" -n --binary "$PYRE_BINARY" analyze --save-results-to out )

mkdir -p "$OUT_DIR"
python3 - "$WORK" "$OUT_DIR" <<'EOF'
import json, sys
work, out_dir = sys.argv[1], sys.argv[2]
run_entry = None
for line in open(f"{work}/out/call-graph.json"):
    entry = json.loads(line)
    if entry.get("kind") == "call_graph" and \
            entry["data"].get("callable") == "dispatch_table.run":
        run_entry = entry["data"]
issues, models = [], []
for line in open(f"{work}/out/taint-output.json"):
    entry = json.loads(line)
    if entry.get("kind") == "issue":
        issues.append(entry["data"])
    if entry.get("kind") == "model" and \
            str(entry["data"].get("callable", "")).startswith("dispatch_table."):
        models.append(entry["data"])
document = {
    "evidence_kind": "retained-probe",
    "probe": "pysa-callee-resolution",
    "fixture": "cases/taint/python/dispatch-table-positive/dispatch_table.py",
    "run_call_graph": run_entry,
    "bound_models": models,
    "issue_count": len(issues),
}
with open(f"{out_dir}/dispatch-table-call-graph.json", "w") as f:
    json.dump(document, f, indent=2)
    f.write("\n")
print(f"wrote {out_dir}/dispatch-table-call-graph.json "
      f"(issues: {len(issues)})")
EOF

#!/usr/bin/env bash
# Amendment A13's evidence: Infer's modeling partition, measured rather than
# assumed.
#
# Infer v1.3.0 joins the benchmark-controlled modeling matrix with its own
# preregistered partition row, and this probe is the field evaluation that row
# is decided from. Every cell below is measured by execution over the committed
# Java modeling fixtures — the acceptance rule is the preregistration's own
# load-bearing-model requirement, not a lowered one: a declared model must
# suppress or enable the flow, its removal must flip it, and an undeclared
# lookalike must not move.
#
# What it measures, per category:
#
#   S  Sources and sinks bind by exact type+member identity
#      (`class_names` + `method_names`); load-bearing by removal; undeclared
#      same-type siblings unmatched.
#   P  Template 3 is load-bearing three ways: the reflective body carries
#      nothing unaided, the declared `Opaque.carry` propagator carries it, and
#      the undeclared identical `Opaque.block` does not. Template 4 is NOT
#      expressible: a Pulse propagator declares an output (`taint_target`) but
#      no input position, and the measured propagator carries taint from the
#      undeclared position 0 exactly as from the declared position 1 — both
#      cells are decided by the any-argument default, not the model. A
#      hypothetical input-position field is silently ignored, so no spelling
#      can be trusted to bind it.
#   Z  The sanitizer stanza suppresses on a completing run, its removal
#      restores the flow, and the undeclared `Clean.sanitize` lookalike is not
#      suppressed. One quirk is retained on purpose: a sanitizer whose kind is
#      not named in a policy's `sanitizer_kinds` is silently inert, which is
#      why the runner's load-bearing gate refuses an unwired artifact.
#   O  Template 7's identity bodies are captured and read: both cells report
#      with no declaration at all, so the cells are decided by body analysis,
#      and `--pulse-taint-opaque-files` — the one candidate body-ignoring
#      surface — is measured inert for Java on the pinned build. Template 8's
#      `FieldsOfValue` destination is not field-precise: the declared
#      `1.payload` summary taints the sibling `spare` too, so the
#      field-separation negative is decided by the heap approximation.
#   E  A source matcher's argument taint_target applies at call boundaries
#      only: declared on the uncalled handler's parameter, the analysis
#      synthesizes no root and reports nothing inside the handler's body.
#   B  No execution probe is possible: the pulse-taint surface defines
#      sources, sinks, sanitizers, propagators, policies, and data-flow kinds
#      and nothing else — the retained `pulse-taint-config-surface.txt` is the
#      binary's own enumeration, with no store-write/store-read vocabulary in
#      it.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome: it retains the verbatim SARIF beside a
# summary of each invocation so the demonstration is auditable on its own.
#
# Usage:
#   scripts/probe-infer-modeling-partition.sh --infer <path> [--javac <path>]
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
OUT="$ROOT/reports/raw/amendment-a13-infer-partition"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

COMMITTED="$ROOT/adapters/infer/config/model-java.json"
CASES="$ROOT/cases/taint/java"

"$INFER" --version | head -1 > "$OUT/witnessed-version.txt"

# The binary's own enumeration of the pulse-taint configuration surface —
# category B's evidence is that no store vocabulary appears anywhere in it.
"$INFER" analyze --help 2>&1 \
  | sed -n '/--pulse-taint-config/,/--pulse-widen-threshold/p' \
  > "$OUT/pulse-taint-config-surface.txt"

# Derived counterfactual and candidate configurations. Counterfactuals strip
# one declaration from the committed artifact and nothing else; candidates add
# a declaration the artifact deliberately does not carry, so a declined
# category's inexpressibility is measured rather than presumed.
python3 - "$COMMITTED" "$SCRATCH" <<'PY'
import json, sys
committed_path, scratch = sys.argv[1], sys.argv[2]
committed = json.load(open(committed_path))

def write(name, config):
    with open(f"{scratch}/{name}.json", "w") as out:
        json.dump(config, out, indent=2)

# S counterfactual: the declared-source entry removed.
without_source = json.loads(json.dumps(committed))
without_source["pulse-taint-sources"] = [
    entry for entry in without_source["pulse-taint-sources"]
    if entry.get("method_names") != ["fetchRemote"]
]
assert len(without_source["pulse-taint-sources"]) == 1
write("without-declared-source", without_source)

# P counterfactual: the propagator section removed.
without_propagator = json.loads(json.dumps(committed))
without_propagator["pulse-taint-propagators"] = []
write("without-propagator", without_propagator)

# P candidate: the template-4 `select` propagator, declared the only way the
# surface allows — with an output position and no input position.
with_select = json.loads(json.dumps(committed))
with_select["pulse-taint-propagators"].append({
    "class_names": ["dataflowbench.taint.Opaque"],
    "method_names": ["select"],
    "taint_target": "ReturnValue",
})
write("with-select-propagator", with_select)

# P candidate: a hypothetical input-position spelling, to show unknown fields
# are silently ignored rather than rejected.
with_select_position = json.loads(json.dumps(with_select))
with_select_position["pulse-taint-propagators"][-1]["argument_positions"] = [1]
write("with-select-propagator-unknown-field", with_select_position)

# Z counterfactual: the sanitizer section removed.
without_sanitizer = json.loads(json.dumps(committed))
without_sanitizer["pulse-taint-sanitizers"] = []
write("without-sanitizer", without_sanitizer)

# Z quirk: the sanitizer declared but its kind not wired into any policy's
# `sanitizer_kinds` — the silently-inert shape the runner's gate refuses.
unwired_sanitizer = json.loads(json.dumps(committed))
for policy in unwired_sanitizer["pulse-taint-policies"]:
    for flow in policy["taint_flows"]:
        flow.pop("sanitizer_kinds", None)
write("with-unwired-sanitizer", unwired_sanitizer)

# O candidate: the template-8 store-through summary, declared through the one
# field-destination surface that exists (`FieldsOfValue` on the second
# argument's `payload`).
with_deposit = json.loads(json.dumps(committed))
with_deposit["pulse-taint-propagators"].append({
    "class_names": ["dataflowbench.taint.Bridge"],
    "method_names": ["deposit"],
    "taint_target": ["FieldsOfValue", [["payload", ["ArgumentPositions", [1]]]]],
})
write("with-deposit-field-summary", with_deposit)

# E candidate: the template-9 entry-point declaration, on the instance
# method's parameter (argument index 1; index 0 is the receiver).
with_entrypoint = json.loads(json.dumps(committed))
with_entrypoint["pulse-taint-sources"].append({
    "class_names": ["dataflowbench.taint.Handler"],
    "method_names": ["onRequest"],
    "taint_target": ["ArgumentPositions", [1]],
    "kinds": ["DataFlowBenchModelSource"],
})
write("with-entrypoint-source", with_entrypoint)
PY

probe() { # <label> <case dir name> <config path> [extra analyze args...]
  local label="$1" case="$2" config="$3"; shift 3
  local work="$SCRATCH/$label"
  rm -rf "$work"
  mkdir -p "$work/dataflowbench/taint"
  cp "$CASES/$case"/*.java "$work/dataflowbench/taint/"
  (
    cd "$work"
    "$INFER" capture --results-dir infer-out -- \
      "$JAVAC" dataflowbench/taint/*.java > capture.log 2>&1
    "$INFER" analyze --results-dir infer-out --pulse-only --sarif \
      --pulse-taint-config "$config" "$@" > analyze.log 2>&1
  )
  cp "$work/infer-out/report.sarif" "$OUT/$label.sarif.json"
  python3 - "$label" "$case" "$config" "$OUT" "$work/infer-out/report.sarif" "$*" <<'PY'
import json, sys
label, case, config, out, sarif_path, extra = sys.argv[1:7]
sarif = json.load(open(sarif_path))
results = [r for run in sarif.get("runs", []) for r in run.get("results", [])]
taint = [r for r in results if r.get("ruleId") == "TAINT_ERROR"]
summary = {
    "probe": label,
    "case": case,
    "configuration": json.load(open(config)),
    "extra_analyze_arguments": extra.split() if extra else [],
    "taint_error_count": len(taint),
    "taint_errors": [
        {
            "uri": r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
            "line": r["locations"][0]["physicalLocation"]["region"]["startLine"],
            "message": r["message"]["text"],
        }
        for r in taint
    ],
    "evidence_kind": "retained-partition-probe",
}
with open(f"{out}/{label}.json", "w") as fh:
    json.dump(summary, fh, indent=2)
    fh.write("\n")
print(f"{label}: taint={len(taint)}")
PY
}

# --- Category S ------------------------------------------------------------
probe s-declared-source-positive-with-model model-declared-source-positive "$COMMITTED"
probe s-declared-source-positive-without-model model-declared-source-positive "$SCRATCH/without-declared-source.json"
probe s-declared-source-negative-with-model model-declared-source-negative "$COMMITTED"
probe s-declared-sink-positive-with-model model-declared-sink-positive "$COMMITTED"
probe s-declared-sink-negative-with-model model-declared-sink-negative "$COMMITTED"

# --- Category P ------------------------------------------------------------
probe p-opaque-propagator-positive-without-model model-opaque-propagator-positive "$SCRATCH/without-propagator.json"
probe p-opaque-propagator-positive-with-model model-opaque-propagator-positive "$COMMITTED"
probe p-opaque-propagator-negative-with-model model-opaque-propagator-negative "$COMMITTED"
probe p-propagator-position-positive-with-select model-propagator-position-positive "$SCRATCH/with-select-propagator.json"
probe p-propagator-position-negative-with-select model-propagator-position-negative "$SCRATCH/with-select-propagator.json"
probe p-propagator-position-negative-unknown-field model-propagator-position-negative "$SCRATCH/with-select-propagator-unknown-field.json"

# --- Category Z ------------------------------------------------------------
probe z-sanitizer-kill-positive-with-model model-sanitizer-kill-positive "$COMMITTED"
probe z-sanitizer-kill-negative-with-model model-sanitizer-kill-negative "$COMMITTED"
probe z-sanitizer-kill-negative-without-model model-sanitizer-kill-negative "$SCRATCH/without-sanitizer.json"
probe z-sanitizer-kill-negative-unwired model-sanitizer-kill-negative "$SCRATCH/with-unwired-sanitizer.json"
probe z-sanitizer-selectivity-positive-with-model model-sanitizer-selectivity-positive "$COMMITTED"
probe z-sanitizer-selectivity-negative-with-model model-sanitizer-selectivity-negative "$COMMITTED"

# --- Category O ------------------------------------------------------------
probe o-summary-through-positive-unmodeled model-summary-through-positive "$COMMITTED"
probe o-summary-through-negative-unmodeled model-summary-through-negative "$COMMITTED"
probe o-summary-through-positive-opaque-files model-summary-through-positive "$COMMITTED" \
  --pulse-taint-opaque-files dataflowbench/taint/Bridge.java
probe o-summary-field-positive-unmodeled model-summary-field-positive "$COMMITTED"
probe o-summary-field-positive-with-field-summary model-summary-field-positive "$SCRATCH/with-deposit-field-summary.json"
probe o-summary-field-negative-with-field-summary model-summary-field-negative "$SCRATCH/with-deposit-field-summary.json"

# --- Category E ------------------------------------------------------------
probe e-entrypoint-parameter-positive-with-source model-entrypoint-parameter-positive "$SCRATCH/with-entrypoint-source.json"

echo "retained field-evaluation evidence under reports/raw/amendment-a13-infer-partition/"

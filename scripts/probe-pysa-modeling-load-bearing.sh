#!/usr/bin/env bash
# Amendment A13's evidence: Pysa's modeling partition row, measured rather
# than assumed, before the adapter's first scored modeling run.
#
# A new adapter joins the modeling matrix with its own preregistered partition
# row, added by amendment (docs/modeling-matrix.md#rollout-plan). This probe is
# that row's field evaluation. It runs the pinned pyre-check 0.10.0 + Pyrefly
# 1.2.0 pair over the committed Python modeling fixtures, template by
# template, in the run-it-twice shape of the per-language load-bearing probes
# beside it: once under the committed block of
# `adapters/pysa/models/modeling-python.pysa`, and once under a counterfactual
# with the declaration under test removed and nothing else changed. Both raw
# outputs are retained.
#
# Two measurements decide the shape of the row:
#
#   1. **The matrix's reflective opaque body is not opaque to this pair.**
#      With the benchmark endpoints declared and *no* propagator model at all,
#      the pinned pair still reports template 3's flow: Pyrefly narrows
#      `getattr(_impl, name)` over the local string constant and resolves the
#      self-dispatch, so the engine's own body reading would decide every
#      category P and O cell. This is the same evidentiary situation Amendment
#      A4 recorded for Joern's frontends, and it is retained here as
#      `opaque-propagator-unmodeled`.
#   2. **`@SkipAnalysis` + `@SkipObscure` are the switch that makes the
#      declarations load-bearing.** Under both modes the declared entity's
#      body is ignored and the obscure taint-through fallback is off, so the
#      taint it carries is exactly what its declaration states. Removing a
#      `TaintInTaintOut` while keeping the skip modes flips the verdict, in
#      category P and in category O — which is what
#      docs/modeling-matrix.md#the-load-bearing-model-requirement requires
#      before either category may be scored.
#
# Every scored category is probed in every direction its templates need:
# activation (the declared model produces the verdict), removal (deleting the
# declaration flips it), and selectivity (an undeclared lookalike is not
# bound). Category B is not probed: the `.pysa` DSL has no store identity,
# key, or cross-procedure link vocabulary, so there is no declaration whose
# activation could be measured.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome.
#
# Usage:
#   scripts/probe-pysa-modeling-load-bearing.sh \
#     --pyre <path> --pyre-binary <path> --pyrefly <path>
set -euo pipefail

PYRE=pyre
PYRE_BINARY=pyre.bin
PYREFLY=pyrefly
while [ $# -gt 0 ]; do
  case "$1" in
    --pyre) PYRE="$2"; shift 2 ;;
    --pyre-binary) PYRE_BINARY="$2"; shift 2 ;;
    --pyrefly) PYREFLY="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a13-pysa-modeling"
ARTIFACT="$ROOT/adapters/pysa/models/modeling-python.pysa"
TAINT_CONFIG="$ROOT/adapters/pysa/taint.config"
CASES="$ROOT/cases/taint/python"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

"$PYRE" --version >/dev/null
"$PYREFLY" --version >/dev/null

# Cut one template's block out of the committed artifact. The markers are the
# same `# template:` lines the runner cuts at, so the probe and the runner
# read the same declarations.
block() { # <template-id>
  python3 - "$ARTIFACT" "$1" <<'PY'
import sys
text = open(sys.argv[1]).read()
marker = f"# template: {sys.argv[2]}\n"
start = text.index(marker) + len(marker)
end = text.find("# template: ", start)
print(text[start:end if end != -1 else len(text)].strip())
PY
}

# One probe direction: materialize the fixture and the given models, run the
# pinned pair, retain the raw taint output, and assert the expectation.
probe() { # <name> <case-dir> <expected: issue|none> ; models on stdin
  local name="$1" case_dir="$2" expected="$3"
  local work="$SCRATCH/$name"
  mkdir -p "$work/src" "$work/models" "$work/out"
  cp "$CASES/$case_dir"/*.py "$work/src/"
  cp "$TAINT_CONFIG" "$work/models/taint.config"
  cat > "$work/models/dfb.pysa"
  printf 'project-includes = ["src/**/*.py"]\n' > "$work/pyrefly.toml"
  printf '{\n  "source_directories": ["src"],\n  "taint_models_path": ["models"]\n}\n' \
    > "$work/.pyre_configuration"
  (
    cd "$work"
    PATH="$(dirname "$PYREFLY"):$PATH" "$PYRE" -n --binary "$PYRE_BINARY" \
      analyze --save-results-to out > pyre-stdout.txt 2> pyre-stderr.txt
  )
  cp "$work/out/taint-output.json" "$OUT/$name.json"
  cp "$work/models/dfb.pysa" "$OUT/$name-models.pysa"
  local issues
  issues="$(python3 - "$OUT/$name.json" <<'PY'
import json, sys
count = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if line and json.loads(line).get("kind") == "issue":
        count += 1
print(count)
PY
)"
  case "$expected" in
    issue) [ "$issues" -ge 1 ] || { echo "$name: expected an issue, saw none" >&2; exit 1; } ;;
    none) [ "$issues" -eq 0 ] || { echo "$name: expected no issue, saw $issues" >&2; exit 1; } ;;
  esac
  echo "$name: $issues issue(s) — expected $expected"
}

# --- Category S: declared sources and sinks -------------------------------
block dfb-template-model-declared-source \
  | probe declared-source-positive model-declared-source-positive issue
block dfb-template-model-declared-source \
  | probe declared-source-negative model-declared-source-negative none
# Removal: the sink stays declared; only the source declaration is deleted.
block dfb-template-model-declared-source | grep -v fetch_remote \
  | probe declared-source-removed model-declared-source-positive none
block dfb-template-model-declared-sink \
  | probe declared-sink-positive model-declared-sink-positive issue
block dfb-template-model-declared-sink \
  | probe declared-sink-negative model-declared-sink-negative none

# --- Category P: declared propagators -------------------------------------
# The opacity measurement: endpoints declared, no propagator model, no skip
# modes — and the pinned pair still follows the reflective body on its own.
printf '%s\n' \
  'def opaque.dfb_source() -> TaintSource[DfbSource]: ...' \
  'def opaque.dfb_sink(value: TaintSink[DfbSink]): ...' \
  | probe opaque-propagator-unmodeled model-opaque-propagator-positive issue
block dfb-template-model-opaque-propagator \
  | probe opaque-propagator-positive model-opaque-propagator-positive issue
block dfb-template-model-opaque-propagator \
  | probe opaque-propagator-negative model-opaque-propagator-negative none
# Removal under the skip modes: the tito is deleted, the modes stay.
block dfb-template-model-opaque-propagator \
  | sed 's/def opaque.carry(value: TaintInTaintOut)/def opaque.carry(value)/' \
  | probe opaque-propagator-tito-removed model-opaque-propagator-positive none
block dfb-template-model-propagator-position \
  | probe propagator-position-positive model-propagator-position-positive issue
block dfb-template-model-propagator-position \
  | probe propagator-position-negative model-propagator-position-negative none

# --- Category Z: declared sanitizers --------------------------------------
block dfb-template-model-sanitizer-kill \
  | probe sanitizer-kill-positive model-sanitizer-kill-positive issue
block dfb-template-model-sanitizer-kill \
  | probe sanitizer-kill-negative model-sanitizer-kill-negative none
# Restoration: the @Sanitize is deleted and the flow through scrub returns.
block dfb-template-model-sanitizer-kill | grep -v '@Sanitize' | grep -v scrub \
  | probe sanitizer-kill-removed model-sanitizer-kill-negative issue
block dfb-template-model-sanitizer-selectivity \
  | probe sanitizer-selectivity-positive model-sanitizer-selectivity-positive issue
block dfb-template-model-sanitizer-selectivity \
  | probe sanitizer-selectivity-negative model-sanitizer-selectivity-negative none

# --- Category O: opaque procedure summaries -------------------------------
block dfb-template-model-summary-through \
  | probe summary-through-positive model-summary-through-positive issue
block dfb-template-model-summary-through \
  | probe summary-through-negative model-summary-through-negative none
block dfb-template-model-summary-through \
  | sed 's/def bridge.pass_through(value: TaintInTaintOut)/def bridge.pass_through(value)/' \
  | probe summary-through-tito-removed model-summary-through-positive none
# The body-reading control: no summary declarations at all, and the engine
# reports the flow from the identity bodies — which is exactly what the
# summaries exist to override, and why the skip modes are mandatory.
printf '%s\n' \
  'def flow.dfb_source() -> TaintSource[DfbSource]: ...' \
  'def flow.dfb_sink(value: TaintSink[DfbSink]): ...' \
  | probe summary-through-body-control model-summary-through-positive issue
block dfb-template-model-summary-field \
  | probe summary-field-positive model-summary-field-positive issue
block dfb-template-model-summary-field \
  | probe summary-field-negative model-summary-field-negative none
block dfb-template-model-summary-field \
  | sed 's/def bridge.deposit(value: TaintInTaintOut\[Updates\[box\], UpdatePath\[_.payload\]\], box)/def bridge.deposit(value, box)/' \
  | probe summary-field-removed model-summary-field-positive none

# --- Category E: framework entry points -----------------------------------
block dfb-template-model-entrypoint-parameter \
  | probe entrypoint-parameter-positive model-entrypoint-parameter-positive issue
block dfb-template-model-entrypoint-parameter \
  | probe entrypoint-parameter-negative model-entrypoint-parameter-negative none
block dfb-template-model-entrypoint-parameter | grep -v on_request \
  | probe entrypoint-parameter-removed model-entrypoint-parameter-positive none
block dfb-template-model-entrypoint-selectivity \
  | probe entrypoint-selectivity-positive model-entrypoint-selectivity-positive issue
block dfb-template-model-entrypoint-selectivity \
  | probe entrypoint-selectivity-negative model-entrypoint-selectivity-negative none

echo "retained under $OUT"

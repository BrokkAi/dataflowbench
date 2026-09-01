#!/usr/bin/env bash
# Amendment A17's evidence: how Pysa's shipped taint models are activated, and
# that they activate at all — measured before the adapter's first tool-native
# run, on the pinned pyre-check 0.10.0 + Pyrefly 1.2.0 pair.
#
# The pinned pyre-check wheel ships a real model suite in its distribution:
# `lib/pyre_check/taint/` carries `core_privacy_security/` (a `taint.config`
# with 35 rules plus the stdlib and framework `.pysa` model files) and
# `common/` (propagation models for builtins and collections). Nothing in it
# is benchmark-authored. Three facts about activating it are established here,
# each retained as raw evidence:
#
#   1. **The shipped product refuses to run with no model path.** `pyre
#      analyze` with no `taint_models_path` fails its own taint-configuration
#      verification (`Found 1 taint configuration error!`, exit 9): there is
#      no ambient default. Pointing `taint_models_path` at the wheel's own
#      `lib/pyre_check/taint` is therefore the activation — a configuration
#      of shipped models, the same kind of switch as CodeQL's
#      `--threat-model=local`, adding no row of ours.
#   2. **The shipped suite does not verify over a stdlib-only project.** Its
#      framework models name definitions a dependency-free fixture does not
#      carry, so strict verification refuses the run (`Found 122 model
#      verification errors!`, exit 10) — and the client's own remediation
#      hint names `--no-verify`. The native invocation therefore carries
#      `--no-verify`, and the activation proof moves from the verifier to the
#      retained evidence itself (direction 3).
#   3. **Under that activation the suite demonstrably binds.** The retained
#      `taint-output.json` for the category-S fixture carries a shipped model
#      for `os.system` — the RemoteCodeExecution sink every Python native
#      template sinks through — so a `not-reached` under this activation is a
#      coverage measurement about the shipped sources, never a silent
#      failure to load the suite.
#
# The probe asserts activation, not outcomes: whatever the shipped sources do
# or do not cover is the run's measurement to publish, and no expectation
# about it is encoded here.
#
# Usage:
#   scripts/probe-pysa-native-activation.sh \
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
OUT="$ROOT/reports/raw/amendment-a17-pysa-native"
CASES="$ROOT/cases/taint/python"
SUITE="$(cd "$(dirname "$PYRE")/.." && pwd)/lib/pyre_check/taint"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

"$PYRE" --version >/dev/null
"$PYREFLY" --version >/dev/null
[ -d "$SUITE" ] || { echo "shipped suite $SUITE does not exist" >&2; exit 1; }

workspace() { # <name> <configuration-json>
  local work="$SCRATCH/$1"
  mkdir -p "$work/src" "$work/out"
  cp "$CASES/native-source-sink-positive"/*.py "$work/src/"
  printf 'project-includes = ["src/**/*.py"]\n' > "$work/pyrefly.toml"
  printf '%s\n' "$2" > "$work/.pyre_configuration"
  echo "$work"
}

run_in() { # <workdir> <extra pyre args...>
  local work="$1"; shift
  (
    cd "$work"
    PATH="$(dirname "$PYREFLY"):$PATH" "$PYRE" -n --binary "$PYRE_BINARY" \
      analyze --save-results-to out "$@" \
      > pyre-stdout.txt 2> pyre-stderr.txt
    echo $? > exit-code.txt
  ) || true
  cat "$work/exit-code.txt"
}

# 1. No taint_models_path: the shipped product refuses, loudly.
W="$(workspace no-model-path '{ "source_directories": ["src"] }')"
code="$(run_in "$W")"
grep -h "taint configuration error" "$W/pyre-stderr.txt" > "$OUT/no-model-path-refusal.txt"
echo "exit $code" >> "$OUT/no-model-path-refusal.txt"
[ "$code" -ne 0 ] || { echo "expected a refusal with no taint_models_path" >&2; exit 1; }
echo "no-model-path: refused (exit $code)"

# 2. Shipped suite under strict verification: refused, with the vendor's hint.
W="$(workspace strict-verify "{ \"source_directories\": [\"src\"], \"taint_models_path\": [\"$SUITE\"] }")"
code="$(run_in "$W")"
grep -h "model verification error\|--no-verify" "$W/pyre-stderr.txt" \
  > "$OUT/strict-verification-refusal.txt"
echo "exit $code" >> "$OUT/strict-verification-refusal.txt"
[ "$code" -ne 0 ] || { echo "expected strict verification to refuse the shipped suite" >&2; exit 1; }
echo "strict-verify: refused (exit $code)"

# 3. The pinned activation: shipped suite, --no-verify. The run completes and
# the retained evidence carries a shipped model for `os.system`.
W="$(workspace shipped-activation "{ \"source_directories\": [\"src\"], \"taint_models_path\": [\"$SUITE\"] }")"
code="$(run_in "$W" --no-verify)"
[ "$code" -eq 0 ] || { echo "the pinned activation failed (exit $code)" >&2; exit 1; }
cp "$W/out/taint-output.json" "$OUT/shipped-activation.json"
python3 - "$OUT/shipped-activation.json" <<'PY'
import json, sys
models = set()
issues = 0
for line in open(sys.argv[1]):
    line = line.strip()
    if not line:
        continue
    entry = json.loads(line)
    if entry.get("kind") == "model":
        models.add(entry["data"].get("callable"))
    elif entry.get("kind") == "issue":
        issues += 1
assert "os.system" in models, "the shipped os.system sink model did not bind"
print(f"shipped-activation: os.system model bound; {issues} issue(s) retained")
PY

echo "retained under $OUT"

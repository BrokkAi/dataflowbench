#!/usr/bin/env bash
# Load-bearing-model demonstration for the JavaScript modeling matrix.
#
# docs/modeling-matrix.md#the-load-bearing-model-requirement says a modeling
# assertion is only evidence of activation if the tool's behavior *without* the
# model would differ. This script demonstrates exactly that, for one scored
# category per adapter: it runs one positive fixture twice, once against the
# committed modeling artifact and once against a copy of that artifact with the
# single declaration under test deleted, and retains both raw outputs.
#
#   Bifrost   category S   the `Config.fetchRemote` source declaration
#   CodeQL    category P   the `Opaque.carry` propagator step
#   Joern     category Z   the `"scrub"` no-flow (sanitizer) declaration
#   Semgrep   category S   the `Audit.record` sink declaration
#
# It also runs one deliberate **counter-example**: Joern's category-P
# declaration, `"carry" 1->-1`, is *not* load-bearing on JavaScript. Removing it
# leaves the finding in place, because the pinned Joern follows the fixture's
# `Reflect.get(_impl, name).apply(null, [v])` body on its own. That pair is
# retained under `joern-opaque-propagator-*-model.json` precisely so the
# published category-P positive is not read as evidence of activation. See
# docs/javascript-modeling.md.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome: it retains raw tool output beside the
# modeling evidence so the demonstration is auditable on its own.
#
# Usage:
#   scripts/probe-javascript-modeling-load-bearing.sh \
#     --bifrost <path> --codeql <path> --joern <path> --semgrep <path>
set -euo pipefail

BIFROST=bifrost
CODEQL=codeql
JOERN=joern
SEMGREP=semgrep
while [ $# -gt 0 ]; do
  case "$1" in
    --bifrost) BIFROST="$2"; shift 2 ;;
    --codeql) CODEQL="$2"; shift 2 ;;
    --joern) JOERN="$2"; shift 2 ;;
    --semgrep) SEMGREP="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/load-bearing-javascript-modeling"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

# ---------------------------------------------------------------------------
# Bifrost — category S, the declared-source activation of template 1.
# ---------------------------------------------------------------------------
BF_CASE="$ROOT/cases/taint/javascript/model-declared-source-positive"
mkdir -p "$SCRATCH/bifrost-with" "$SCRATCH/bifrost-without"
cp "$BF_CASE"/*.js "$SCRATCH/bifrost-with/"
cp "$BF_CASE"/*.js "$SCRATCH/bifrost-without/"
cp "$ROOT/adapters/bifrost/policies/model-javascript.rqlp" "$SCRATCH/bifrost-with/policy.rqlp"
grep -v 'declared-source' "$ROOT/adapters/bifrost/policies/model-javascript.rqlp" \
  > "$SCRATCH/bifrost-without/policy.rqlp"
for variant in with without; do
  "$BIFROST" --root "$SCRATCH/bifrost-$variant" --policy-file policy.rqlp \
    --evaluation-date 2026-08-11 --format json --fail-on never \
    --output "$OUT/bifrost-declared-source-$variant-model.json" || true
done

# ---------------------------------------------------------------------------
# CodeQL — category P, the opaque-propagator activation of template 3.
# ---------------------------------------------------------------------------
CQ_CASE="$ROOT/cases/taint/javascript/model-opaque-propagator-positive"
mkdir -p "$SCRATCH/codeql-source"
cp "$CQ_CASE"/*.js "$SCRATCH/codeql-source/"
cp -R "$ROOT/adapters/codeql/javascript" "$SCRATCH/codeql-pack"
# Delete the four-line `carry` propagator clause and the `or` that joins it.
python3 - "$SCRATCH/codeql-pack/queries/JavaScriptModeling.ql" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path).read()
clause = """    exists(DataFlow::CallNode call |
      call.getCalleeName() = "carry" and
      node1 = call.getArgument(0) and
      node2 = call and
      isJavaScriptFixture(node1)
    )
    or
"""
if clause not in text:
    raise SystemExit("the carry propagator clause is not where the probe expects it")
open(path, "w").write(text.replace(clause, "", 1))
PY
"$CODEQL" database create "$SCRATCH/codeql-db" --language=javascript \
  --source-root="$SCRATCH/codeql-source" --overwrite > /dev/null
for variant in with without; do
  if [ "$variant" = with ]; then
    QUERY="$ROOT/adapters/codeql/javascript/queries/JavaScriptModeling.ql"
  else
    QUERY="$SCRATCH/codeql-pack/queries/JavaScriptModeling.ql"
  fi
  "$CODEQL" database analyze "$SCRATCH/codeql-db" "$QUERY" --format=sarif-latest \
    --output="$OUT/codeql-opaque-propagator-$variant-model.sarif.json" --rerun > /dev/null
done

# ---------------------------------------------------------------------------
# Joern — category Z, the declared sanitizer of template 5's negative, and the
# category-P counter-example.
# ---------------------------------------------------------------------------
SEMANTICS="$ROOT/adapters/joern/semantics/model-javascript.semantics"
mkdir -p "$SCRATCH/joern-run"
cp "$SEMANTICS" "$SCRATCH/with.semantics"
grep -v '^"scrub"' "$SEMANTICS" > "$SCRATCH/no-scrub.semantics"
grep -v '^"carry"' "$SEMANTICS" > "$SCRATCH/no-carry.semantics"
joern_probe() { # <fixture case dir> <semantics file> <output name>
  rm -rf "$SCRATCH/joern-source"
  mkdir -p "$SCRATCH/joern-source"
  cp "$1"/*.js "$SCRATCH/joern-source/"
  ( cd "$SCRATCH/joern-run" && "$JOERN" --script "$ROOT/adapters/joern/queries/modeling.sc" \
      --param "inputPath=$SCRATCH/joern-source" \
      --param language=JSSRC \
      --param "semanticsPath=$2" \
      --param "outputPath=$OUT/$3" \
      < /dev/null > /dev/null )
  rm -rf "$SCRATCH/joern-run/workspace"
}
JZ_CASE="$ROOT/cases/taint/javascript/model-sanitizer-kill-negative"
joern_probe "$JZ_CASE" "$SCRATCH/with.semantics" joern-sanitizer-kill-with-model.json
joern_probe "$JZ_CASE" "$SCRATCH/no-scrub.semantics" joern-sanitizer-kill-without-model.json
# The counter-example: category P is *not* load-bearing for Joern here.
joern_probe "$CQ_CASE" "$SCRATCH/with.semantics" joern-opaque-propagator-with-model.json
joern_probe "$CQ_CASE" "$SCRATCH/no-carry.semantics" joern-opaque-propagator-without-model.json

# ---------------------------------------------------------------------------
# Semgrep — category S, the declared-sink activation of template 2.
# ---------------------------------------------------------------------------
SG_CASE="$ROOT/cases/taint/javascript/model-declared-sink-positive"
mkdir -p "$SCRATCH/semgrep-source"
cp "$SG_CASE"/*.js "$SCRATCH/semgrep-source/"
cp "$ROOT/adapters/semgrep/rules/model-javascript.yaml" "$SCRATCH/with.yaml"
grep -v 'pattern: Audit.record' "$ROOT/adapters/semgrep/rules/model-javascript.yaml" \
  > "$SCRATCH/without.yaml"
for variant in with without; do
  "$SEMGREP" scan --metrics=off --oss-only --disable-version-check --no-git-ignore \
    --quiet --json --config "$SCRATCH/$variant.yaml" "$SCRATCH/semgrep-source" \
    > "$OUT/semgrep-declared-sink-$variant-model.json"
done

echo "retained load-bearing probe evidence under reports/raw/load-bearing-javascript-modeling/"

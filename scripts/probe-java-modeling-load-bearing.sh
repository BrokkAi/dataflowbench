#!/usr/bin/env bash
# Load-bearing-model demonstration for the Java modeling matrix.
#
# The Java counterpart of scripts/probe-javascript-modeling-load-bearing.sh,
# and deliberately the same shape: docs/modeling-matrix.md#the-load-bearing-model-requirement
# says a modeling assertion is only evidence of activation if the tool's
# behavior *without* the model would differ, so this script runs one fixture
# twice — once against the committed modeling artifact and once against a copy
# with the single declaration under test deleted — and retains both raw
# outputs.
#
#   Bifrost   category S   the `Config.fetchRemote` source declaration
#   CodeQL    category P   the `Opaque.carry` propagator step
#   Joern     category Z   the `Clean.scrub` no-flow (sanitizer) declaration
#   Semgrep   category S   the `Audit.record` sink declaration
#
# It also runs two measurements that are not counterfactuals:
#
#   * **Amendment A5's evidence.** The preregistration recorded Bifrost's
#     `:unmodeled require-model` setting as *to be verified* — no committed
#     policy set it and the pinned CLI's acceptance of it was unshown. The
#     `bifrost-require-model-accepted.json` run is the committed policy, which
#     sets it, evaluated to completion on the pinned v0.10.6.
#   * **Amendment A4's evidence, extended to `javasrc2cpg`.** A4 withdrew the
#     preregistration's claim that the reflective opaque-propagator body is
#     unfollowable, on `jssrc2cpg`. `joern-opaque-propagator-unmodeled.json`
#     runs Java's template-3 positive under the committed Java semantics —
#     which, after A2, declares nothing whatsoever for category P — and shows
#     the same thing for the Java frontend, so A4's correction is not
#     jssrc2cpg-specific.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome: it retains raw tool output beside the
# modeling evidence so the demonstration is auditable on its own.
#
# Usage:
#   scripts/probe-java-modeling-load-bearing.sh \
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
OUT="$ROOT/reports/raw/load-bearing-java-modeling"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$OUT"

# ---------------------------------------------------------------------------
# Bifrost — category S, the declared-source activation of template 1, and
# Amendment A5's `require-model` acceptance on the same run.
# ---------------------------------------------------------------------------
BF_CASE="$ROOT/cases/taint/java/model-declared-source-positive"
mkdir -p "$SCRATCH/bifrost-with" "$SCRATCH/bifrost-without"
cp "$BF_CASE"/*.java "$SCRATCH/bifrost-with/"
cp "$BF_CASE"/*.java "$SCRATCH/bifrost-without/"
cp "$ROOT/adapters/bifrost/policies/model-java.rqlp" "$SCRATCH/bifrost-with/policy.rqlp"
# Strip only the `(source :id declared-source ...)` entry, leaving the `])`
# that closes the entries vector and the endpoint-set in place — deleting the
# whole line makes the policy unparseable, which would be a probe failure
# rather than a measurement.
python3 - "$ROOT/adapters/bifrost/policies/model-java.rqlp" \
  "$SCRATCH/bifrost-without/policy.rqlp" <<'PY'
import sys
source, destination = sys.argv[1], sys.argv[2]
lines = open(source).read().splitlines(keepends=True)
for index, line in enumerate(lines):
    if ":id declared-source" in line:
        lines[index] = line[: line.index("(source")] + line[line.rindex("])") :]
        break
else:
    raise SystemExit("the declared-source entry is not where the probe expects it")
open(destination, "w").writelines(lines)
PY
for variant in with without; do
  "$BIFROST" --root "$SCRATCH/bifrost-$variant" --policy-file policy.rqlp \
    --evaluation-date 2026-08-11 --format json --fail-on never \
    --output "$OUT/bifrost-declared-source-$variant-model.json" || true
done
# Amendment A5: the committed policy sets `:unmodeled require-model`, and the
# pinned CLI evaluates it rather than rejecting the setting. Retained as its
# own document so the acceptance is auditable without reading the run.
cp "$OUT/bifrost-declared-source-with-model.json" \
  "$OUT/bifrost-require-model-accepted.json"

# ---------------------------------------------------------------------------
# CodeQL — category P, the opaque-propagator activation of template 3. The
# Java extractor has no `--build-mode=none`, so the database is built from a
# traced `javac`, exactly as the modeling runner builds it.
# ---------------------------------------------------------------------------
CQ_CASE="$ROOT/cases/taint/java/model-opaque-propagator-positive"
mkdir -p "$SCRATCH/codeql-source"
cp "$CQ_CASE"/*.java "$SCRATCH/codeql-source/"
mkdir -p "$SCRATCH/codeql-pack/queries"
cp "$ROOT/adapters/codeql/qlpack.yml" "$SCRATCH/codeql-pack/"
cp "$ROOT/adapters/codeql/codeql-pack.lock.yml" "$SCRATCH/codeql-pack/" 2>/dev/null || true
cp "$ROOT/adapters/codeql/queries/JavaModeling.ql" "$SCRATCH/codeql-pack/queries/"
# Delete the five-line `Opaque.carry` propagator clause and the `or` that joins
# it to the next one.
python3 - "$SCRATCH/codeql-pack/queries/JavaModeling.ql" <<'PY'
import sys
path = sys.argv[1]
text = open(path).read()
clause = """    exists(MethodCall call |
      modelCall(call, "Opaque", "carry") and
      node1.asExpr() = call.getArgument(0) and
      node2.asExpr() = call
    )
    or
"""
if clause not in text:
    raise SystemExit("the carry propagator clause is not where the probe expects it")
open(path, "w").write(text.replace(clause, "", 1))
PY
FIXTURES="$(cd "$SCRATCH/codeql-source" && ls ./*.java | tr '\n' ' ')"
"$CODEQL" database create "$SCRATCH/codeql-db" --language=java \
  --source-root="$SCRATCH/codeql-source" --overwrite \
  --command="javac -d classes $FIXTURES" > /dev/null
for variant in with without; do
  if [ "$variant" = with ]; then
    QUERY="$ROOT/adapters/codeql/queries/JavaModeling.ql"
  else
    QUERY="$SCRATCH/codeql-pack/queries/JavaModeling.ql"
  fi
  "$CODEQL" database analyze "$SCRATCH/codeql-db" "$QUERY" --format=sarif-latest \
    --output="$OUT/codeql-opaque-propagator-$variant-model.sarif.json" --rerun > /dev/null
done

# ---------------------------------------------------------------------------
# Joern — category Z, the declared sanitizer of template 5's negative, and the
# category-P counter-example that extends Amendment A4 to `javasrc2cpg`.
# ---------------------------------------------------------------------------
SEMANTICS="$ROOT/adapters/joern/semantics/model-java.semantics"
mkdir -p "$SCRATCH/joern-run"
cp "$SEMANTICS" "$SCRATCH/with.semantics"
grep -v '^"dataflowbench.taint.Clean.scrub' "$SEMANTICS" > "$SCRATCH/no-scrub.semantics"
joern_probe() { # <fixture case dir> <semantics file> <source> <sink> <kind> <output name>
  rm -rf "$SCRATCH/joern-source"
  mkdir -p "$SCRATCH/joern-source"
  cp "$1"/*.java "$SCRATCH/joern-source/"
  ( cd "$SCRATCH/joern-run" && "$JOERN" --script "$ROOT/adapters/joern/queries/modeling.sc" \
      --param "inputPath=$SCRATCH/joern-source" \
      --param language=JAVASRC \
      --param "sourceName=$3" \
      --param "sinkName=$4" \
      --param "sourceKind=$5" \
      --param "semanticsPath=$2" \
      --param "outputPath=$OUT/$6" \
      < /dev/null > /dev/null )
  rm -rf "$SCRATCH/joern-run/workspace"
}
JZ_CASE="$ROOT/cases/taint/java/model-sanitizer-kill-negative"
joern_probe "$JZ_CASE" "$SCRATCH/with.semantics" dfb_source dfb_sink call-return \
  joern-sanitizer-kill-with-model.json
joern_probe "$JZ_CASE" "$SCRATCH/no-scrub.semantics" dfb_source dfb_sink call-return \
  joern-sanitizer-kill-without-model.json
# Amendment A4, extended: category P is declared nowhere in the committed Java
# semantics either, and the reflective body is followed anyway.
joern_probe "$CQ_CASE" "$SCRATCH/with.semantics" dfb_source dfb_sink call-return \
  joern-opaque-propagator-unmodeled.json

# ---------------------------------------------------------------------------
# Semgrep — category S, the declared-sink activation of template 2.
# ---------------------------------------------------------------------------
SG_CASE="$ROOT/cases/taint/java/model-declared-sink-positive"
mkdir -p "$SCRATCH/semgrep-source"
cp "$SG_CASE"/*.java "$SCRATCH/semgrep-source/"
cp "$ROOT/adapters/semgrep/rules/model-java.yaml" "$SCRATCH/with.yaml"
grep -v 'pattern: Audit.record' "$ROOT/adapters/semgrep/rules/model-java.yaml" \
  > "$SCRATCH/without.yaml"
for variant in with without; do
  "$SEMGREP" scan --metrics=off --oss-only --disable-version-check --no-git-ignore \
    --quiet --json --config "$SCRATCH/$variant.yaml" "$SCRATCH/semgrep-source" \
    > "$OUT/semgrep-declared-sink-$variant-model.json"
done

echo "retained load-bearing probe evidence under reports/raw/load-bearing-java-modeling/"

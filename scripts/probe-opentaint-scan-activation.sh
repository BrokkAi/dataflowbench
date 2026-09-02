#!/usr/bin/env bash
# Amendment A25's evidence: the shipped OpenTaint product's own scan entry
# point — `opentaint scan`, the invocation the vendor's demo repository
# documents — activates a versioned builtin rule set, and that rule set,
# field-evaluated against the pinned analyzer over all twelve Java tool-native
# fixtures, loads cleanly and stays silent on every one of them.
#
# Amendment A23 declined OpenTaint's six native cells on the grounds that the
# pinned analyzer release ships no rule set. The vendor's shipped `opentaint`
# CLI complicates that ground without changing the outcome: its `scan` command
# defaults to `--ruleset builtin`, which resolves to the vendor's own
# digest-pinnable rules release (`rules/v0.3.0`, asset
# `opentaint-rules.tar.gz`) and hands it to the same analyzer jar through the
# same `--semgrep-rule-set` flag the benchmark uses. That rule set is shipped
# product, so the decline cannot rest on "no rule set ships" — it has to be
# re-decided against what the shipped rules actually bind.
#
# This probe does exactly that, in the demo-shaped invocation:
#
#   1. All three artifacts are digest-verified: the pinned analyzer jar, the
#      pinned models archive, and the `rules/v0.3.0` archive.
#   2. Each of the twelve committed Java tool-native fixtures is compiled and
#      analyzed by the pinned analyzer with the models archive loaded and the
#      full vendored java rule set active — every severity, a superset of the
#      CLI's warning+error default, so silence here implies silence under the
#      product's own filter.
#   3. The rule-load-trace guard applies: the analyzer exits zero and writes a
#      well-formed empty SARIF even when rules fail to load, so every retained
#      trace must show the rules registered with zero load errors — the
#      silence is proven loaded-and-silent, never swallowed.
#   4. A positive control proves the harness live: a servlet-shaped fixture
#      carrying the real `jakarta.servlet.http` identities (stub classes on
#      the real package path, so the bytecode identity is the one the rules
#      name) flows `request.getParameter(...)` into `Runtime.exec(...)`, and
#      the shipped `os-command-injection` rule reports it under the identical
#      jar, models, rule set, and flags.
#
# The retained outcome: 86 rules registered, zero load errors, zero results on
# all twelve fixtures, one result on the control. The shipped rule set binds
# this profile's command sink (`Runtime.exec`) and no source any native
# template reads — every source rule in it is servlet-, Spring-, or
# Seam-shaped. That is the measured ground the six cells now decline on.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome. Raw outputs land in
# reports/raw/amendment-a25-opentaint-scan-activation/.
#
# Usage:
#   scripts/probe-opentaint-scan-activation.sh \
#     --analyzer-jar <opentaint-project-analyzer.jar> \
#     --models-archive <opentaint-models.tar.gz> \
#     --rules-archive <opentaint-rules.tar.gz> \
#     [--java java] [--javac javac]
#
# The rules archive is the one asset of the vendor's `rules/v0.3.0` release:
#   gh release download rules/v0.3.0 --repo seqra/opentaint \
#     --pattern 'opentaint-rules.tar.gz'
set -euo pipefail

JAVA=java
JAVAC=javac
ANALYZER=""
MODELS_ARCHIVE=""
RULES_ARCHIVE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --analyzer-jar) ANALYZER="$2"; shift 2 ;;
    --models-archive) MODELS_ARCHIVE="$2"; shift 2 ;;
    --rules-archive) RULES_ARCHIVE="$2"; shift 2 ;;
    --java) JAVA="$2"; shift 2 ;;
    --javac) JAVAC="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$ANALYZER" ] || [ -z "$MODELS_ARCHIVE" ] || [ -z "$RULES_ARCHIVE" ]; then
  echo "--analyzer-jar, --models-archive and --rules-archive are required" >&2
  exit 2
fi

EXPECTED_JAR_SHA256=811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54
EXPECTED_MODELS_SHA256=c2a8fb0bbc3b6d59ed6db0c62732ff9a6f0f491d515cc2247932f2dd78cbb9f5
EXPECTED_RULES_SHA256=3d789c9986479fec792333329abe737eccb15bc06fc59a978a58810118ca1d21
ACTUAL=$(shasum -a 256 "$ANALYZER" | cut -d' ' -f1)
if [ "$ACTUAL" != "$EXPECTED_JAR_SHA256" ]; then
  echo "analyzer jar sha256 $ACTUAL is not the pinned $EXPECTED_JAR_SHA256" >&2
  exit 2
fi
ACTUAL=$(shasum -a 256 "$MODELS_ARCHIVE" | cut -d' ' -f1)
if [ "$ACTUAL" != "$EXPECTED_MODELS_SHA256" ]; then
  echo "models archive sha256 $ACTUAL is not the pinned $EXPECTED_MODELS_SHA256" >&2
  exit 2
fi
ACTUAL=$(shasum -a 256 "$RULES_ARCHIVE" | cut -d' ' -f1)
if [ "$ACTUAL" != "$EXPECTED_RULES_SHA256" ]; then
  echo "rules archive sha256 $ACTUAL is not the pinned $EXPECTED_RULES_SHA256" >&2
  exit 2
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/reports/raw/amendment-a25-opentaint-scan-activation"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT" "$WORK/models" "$WORK/rules"

tar xzf "$MODELS_ARCHIVE" -C "$WORK/models"
tar xzf "$RULES_ARCHIVE" -C "$WORK/rules"

{
  echo "analyzer-jar sha256: $EXPECTED_JAR_SHA256"
  echo "models-archive sha256: $EXPECTED_MODELS_SHA256"
  echo "rules-archive sha256: $EXPECTED_RULES_SHA256 (seqra/opentaint release rules/v0.3.0, asset opentaint-rules.tar.gz)"
} > "$OUT/witnessed-identity.txt"

run_analyzer() {
  local case_dir="$1" case_id="$2"
  "$JAVA" -jar "$ANALYZER" \
    --project="$case_dir/project.yaml" \
    --project-kind=unknown \
    "--debug-run-analysis-on-selected-entry-points=*" \
    --semgrep-rule-set="$WORK/rules/java" \
    --semgrep-rule-load-trace="$case_dir/out/load-trace.json" \
    --passthrough-approximations="$WORK/models/java/accumulated-fields.yaml" \
    --passthrough-approximations="$WORK/models/java/config" \
    --java-dataflow-approximations="$WORK/models/java/dataflow/build/classes/java/main" \
    --output-dir="$case_dir/out" > "$case_dir/out/stdout.log"
  cp "$case_dir/out/report-ifds.sarif" "$OUT/$case_id.sarif.json"
  cp "$case_dir/out/load-trace.json" "$OUT/$case_id-load-trace.json"
}

for fixture_dir in "$ROOT"/cases/taint/java/native-*; do
  case_id=$(basename "$fixture_dir")
  case_dir="$WORK/$case_id"
  mkdir -p "$case_dir/source/dataflowbench/taint" "$case_dir/classes" "$case_dir/out"
  cp "$fixture_dir"/*.java "$case_dir/source/dataflowbench/taint/"
  "$JAVAC" -nowarn -d "$case_dir/classes" "$case_dir"/source/dataflowbench/taint/*.java
  cat > "$case_dir/project.yaml" <<EOF
javaProjects:
  - sourceRoot: $case_dir/source
    modules:
      - moduleSourceRoot: $case_dir/source
        packages:
          - dataflowbench.taint
        moduleClasses:
          - $case_dir/classes
EOF
  run_analyzer "$case_dir" "$case_id"
done

# The positive control: real jakarta.servlet.http identities (stubs on the
# real package path, so the compiled bytecode carries the fully-qualified
# names the shipped source rules bind), request parameter into Runtime.exec.
CONTROL="$WORK/control-servlet"
mkdir -p "$CONTROL/source/jakarta/servlet/http" "$CONTROL/source/dataflowbench/control" \
  "$CONTROL/classes" "$CONTROL/out"
cat > "$CONTROL/source/jakarta/servlet/http/HttpServlet.java" <<'EOF'
package jakarta.servlet.http;

public abstract class HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp)
            throws java.io.IOException {
    }
}
EOF
cat > "$CONTROL/source/jakarta/servlet/http/HttpServletRequest.java" <<'EOF'
package jakarta.servlet.http;

public interface HttpServletRequest {
    String getParameter(String name);
}
EOF
cat > "$CONTROL/source/jakarta/servlet/http/HttpServletResponse.java" <<'EOF'
package jakarta.servlet.http;

public interface HttpServletResponse {
}
EOF
cat > "$CONTROL/source/dataflowbench/control/ControlServlet.java" <<'EOF'
package dataflowbench.control;

import jakarta.servlet.http.HttpServlet;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

public class ControlServlet extends HttpServlet {
    @Override
    @SuppressWarnings("deprecation")
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws java.io.IOException {
        String cmd = request.getParameter("cmd");
        Runtime.getRuntime().exec(cmd);
    }
}
EOF
"$JAVAC" -nowarn -d "$CONTROL/classes" \
  "$CONTROL"/source/jakarta/servlet/http/*.java \
  "$CONTROL"/source/dataflowbench/control/*.java
cat > "$CONTROL/project.yaml" <<EOF
javaProjects:
  - sourceRoot: $CONTROL/source
    modules:
      - moduleSourceRoot: $CONTROL/source
        packages:
          - dataflowbench.control
        moduleClasses:
          - $CONTROL/classes
EOF
run_analyzer "$CONTROL" "control-servlet"
cp "$CONTROL/source/dataflowbench/control/ControlServlet.java" "$OUT/control-servlet-fixture.java"

echo "retained probe evidence in reports/raw/amendment-a25-opentaint-scan-activation/"
python3 - "$OUT" <<'EOF'
import glob
import json
import os
import sys

out = sys.argv[1]
failed = False
for sarif_path in sorted(glob.glob(os.path.join(out, "*.sarif.json"))):
    case_id = os.path.basename(sarif_path)[: -len(".sarif.json")]
    sarif = json.load(open(sarif_path))
    trace = json.load(open(os.path.join(out, case_id + "-load-trace.json")))
    load_errors = 0
    rule_traces = 0
    for file_trace in trace["fileTraces"]:
        for entry in file_trace.get("entries", []):
            if entry["type"] == "Error":
                load_errors += 1
        for rule_trace in file_trace.get("ruleTraces", []):
            rule_traces += 1
            for entry in rule_trace.get("entries", []):
                if entry["type"] == "Error":
                    load_errors += 1
    for run in sarif["runs"]:
        rules = run["tool"]["driver"].get("rules", [])
        results = run.get("results", [])
        print(
            f"{case_id}: registered rules: {len(rules)}; rule traces: {rule_traces}; "
            f"load errors: {load_errors}; results: {len(results)}"
        )
        if load_errors:
            failed = True
        if case_id == "control-servlet" and len(results) != 1:
            failed = True
        if case_id != "control-servlet" and results:
            print(f"  UNEXPECTED FINDINGS in {case_id}")
if failed:
    print("PROBE INVARIANT VIOLATED: load errors, or the control did not fire")
    sys.exit(1)
EOF

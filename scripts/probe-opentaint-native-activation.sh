#!/usr/bin/env bash
# The OpenTaint native-activation probe: the field evaluation behind Amendment
# A23's tool-native partition row for OpenTaint in docs/native-profile.md.
#
# The question the tool-native profile asks of a pinned release is what its
# *shipped* model set activates with no benchmark-authored declaration of any
# kind. For OpenTaint the pinned release ships exactly two assets: the
# analyzer jar and `opentaint-models.tar.gz`. The archive is the vendor's own
# platform model set — `passThrough`/`copy` propagation entries, accumulated
# field approximations, and compiled dataflow-approximation classes — and
# declares no source, no sink, and no sanitizer anywhere. The rule set every
# endpoint lives in arrives only through `--semgrep-rule-set`, and the pinned
# release ships none.
#
# This probe runs the pinned analyzer over the committed Java
# `native-source-sink-positive` fixture — `System.getenv` into
# `Runtime.exec`, the floor of the native profile — with the shipped models
# archive loaded and **no rule set supplied**, which is the only activation
# shape the release's own assets can produce. The retained SARIF shows zero
# registered rules and zero results: propagation with no endpoints carries
# nothing anywhere, which is the fact all six of the partition row's cells
# rest on.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome. Raw outputs land in
# reports/raw/opentaint-native-activation-probe/.
#
# Usage:
#   scripts/probe-opentaint-native-activation.sh \
#     --analyzer-jar <opentaint-project-analyzer.jar> \
#     --models-archive <opentaint-models.tar.gz> \
#     [--java java] [--javac javac]
set -euo pipefail

JAVA=java
JAVAC=javac
ANALYZER=""
MODELS_ARCHIVE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --analyzer-jar) ANALYZER="$2"; shift 2 ;;
    --models-archive) MODELS_ARCHIVE="$2"; shift 2 ;;
    --java) JAVA="$2"; shift 2 ;;
    --javac) JAVAC="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$ANALYZER" ] || [ -z "$MODELS_ARCHIVE" ]; then
  echo "--analyzer-jar and --models-archive are required" >&2
  exit 2
fi

EXPECTED_JAR_SHA256=811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54
EXPECTED_MODELS_SHA256=c2a8fb0bbc3b6d59ed6db0c62732ff9a6f0f491d515cc2247932f2dd78cbb9f5
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

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/reports/raw/opentaint-native-activation-probe"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT" "$WORK/source/dataflowbench/taint" "$WORK/classes" "$WORK/out" "$WORK/models"

tar xzf "$MODELS_ARCHIVE" -C "$WORK/models"
cp "$ROOT"/cases/taint/java/native-source-sink-positive/*.java \
  "$WORK/source/dataflowbench/taint/"
"$JAVAC" -nowarn -d "$WORK/classes" "$WORK"/source/dataflowbench/taint/*.java

cat > "$WORK/project.yaml" <<EOF
javaProjects:
  - sourceRoot: $WORK/source
    modules:
      - moduleSourceRoot: $WORK/source
        packages:
          - dataflowbench.taint
        moduleClasses:
          - $WORK/classes
EOF

"$JAVA" -jar "$ANALYZER" \
  --project="$WORK/project.yaml" \
  --project-kind=unknown \
  "--debug-run-analysis-on-selected-entry-points=*" \
  --passthrough-approximations="$WORK/models/java/accumulated-fields.yaml" \
  --passthrough-approximations="$WORK/models/java/config" \
  --java-dataflow-approximations="$WORK/models/java/dataflow/build/classes/java/main" \
  --output-dir="$WORK/out" > "$WORK/out/stdout.log"

cp "$WORK/out/report-ifds.sarif" "$OUT/report-ifds.sarif"

echo "retained probe evidence in reports/raw/opentaint-native-activation-probe/"
python3 - "$OUT" <<'EOF'
import json, sys
sarif = json.load(open(sys.argv[1] + "/report-ifds.sarif"))
for run in sarif["runs"]:
    rules = run["tool"]["driver"].get("rules", [])
    results = run.get("results", [])
    print(f"registered rules: {len(rules)}; results: {len(results)}")
EOF

#!/usr/bin/env bash
# Field evaluation and load-bearing-model demonstration for FlowDroid's Java
# modeling partition (docs/modeling-matrix.md, Amendment A13).
#
# docs/modeling-matrix.md#the-load-bearing-model-requirement says a modeling
# assertion is only evidence of activation if the tool's behavior *without*
# the model would differ, and the amendment contract says a new adapter's
# partition row is preregistered on retained probe evidence. This script is
# that evidence: it materializes the committed Java modeling fixtures into
# the same minimal APKs the adapter's runner builds (javac -> D8 -> stored
# zip with the committed binary manifest), runs the pinned FlowDroid CLI
# over them, and retains one JSON document per probe under
# reports/raw/load-bearing-java-modeling/flowdroid-*.json.
#
# What is demonstrated, per category:
#
#   P  template 3's `Opaque.carry` StubDroid summary is load-bearing: the
#      positive leaks under the committed summaries and stops leaking when
#      the carry flow is deleted (the reflective body carries nothing on the
#      pinned default configuration).
#   P  template 4's positional binding is native: the `select` summary names
#      parameter 1 only, the declared-position positive leaks, and the
#      undeclared-position negative does not.
#   Z  template 5's `Clean.scrub` `<clear>` declaration suppresses the flow
#      on a completing run, and deleting it restores the flow through
#      scrub's identity body.
#   Z  template 6 is *undecidable by construction*: under the same committed
#      Clean summary, the flow through the UNDECLARED sibling `sanitize` is
#      also suppressed, because the summary resolution is exclusive for the
#      whole declaring class (SummaryTaintWrapper.isExclusive answers true
#      whenever `resp.isClassSupported()`), so suppression of the declared
#      sanitizer and selectivity for its undeclared sibling cannot coexist
#      in one invocation. This is the measurement Amendment A13's
#      template-level override rests on.
#   O  template 8's field-destination access path is honored: the declared
#      `deposit` summary (`in: 0`, `out: 1.payload`) reaches the sink that
#      reads `box.payload`, leaves the sibling `box.spare` clean, and
#      deleting the flow removes the positive (deposit's body writes
#      nothing).
#   E  the released CLI has no entry-root declaration surface: an XML
#      sources-and-sinks definition binding `Handler.onRequest`'s parameter
#      as a source parses ("Loaded 1 sources"), and the analysis still finds
#      zero sources, because entry points come exclusively from the APK
#      manifest's Android components and a declaration cannot create a root.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome: it retains raw analyzer output beside
# the other modeling probes so the demonstration is auditable on its own.
#
# Usage:
#   scripts/probe-flowdroid-modeling-load-bearing.sh \
#     --flowdroid-jar <jar> --android-platform <android.jar> --d8-jar <r8.jar> \
#     [--java java] [--javac javac]
set -euo pipefail

FLOWDROID_JAR=""
ANDROID_PLATFORM=""
D8_JAR=""
JAVA=java
JAVAC=javac
while [ $# -gt 0 ]; do
  case "$1" in
    --flowdroid-jar) FLOWDROID_JAR="$2"; shift 2 ;;
    --android-platform) ANDROID_PLATFORM="$2"; shift 2 ;;
    --d8-jar) D8_JAR="$2"; shift 2 ;;
    --java) JAVA="$2"; shift 2 ;;
    --javac) JAVAC="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$FLOWDROID_JAR" ] && [ -n "$ANDROID_PLATFORM" ] && [ -n "$D8_JAR" ] || {
  echo "usage: $0 --flowdroid-jar <jar> --android-platform <android.jar> --d8-jar <r8.jar>" >&2
  exit 2
}

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EVIDENCE="$ROOT/reports/raw/load-bearing-java-modeling"
SUMMARIES="$ROOT/adapters/flowdroid/summaries/model-java"
TEMPLATES="$ROOT/adapters/flowdroid/template"
CASES="$ROOT/cases/taint/java"
mkdir -p "$EVIDENCE"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT

# Materialize one case's APK and run FlowDroid over it.
#   run_probe <evidence-name> <case-dir> <entry-call> <sources-sinks-file> \
#             <summaries-dir-or-NONE> <model-description>
run_probe() {
  local name="$1" case_dir="$2" entry_call="$3" endpoints="$4" summaries="$5" model="$6"
  local work="$SCRATCH/$name"
  mkdir -p "$work/source/dataflowbench/taint" "$work/classes"
  cp "$CASES/$case_dir"/*.java "$work/source/dataflowbench/taint/"
  sed -e "s/__DFB_PACKAGE__/dataflowbench.taint/" \
      -e "s/__DFB_ENTRY_CALL__/$entry_call/" \
      "$TEMPLATES/DfbCaseActivity.java.tmpl" \
      > "$work/source/dataflowbench/taint/DfbCaseActivity.java"
  "$JAVAC" -nowarn -cp "$ANDROID_PLATFORM" -d "$work/classes" \
    "$work/source/dataflowbench/taint"/*.java
  "$JAVA" -cp "$D8_JAR" com.android.tools.r8.D8 --release --min-api 21 \
    --lib "$ANDROID_PLATFORM" --output "$work" \
    $(find "$work/classes" -name '*.class') >/dev/null 2>&1
  cp "$TEMPLATES/AndroidManifest-java.xml" "$work/AndroidManifest.xml"
  (cd "$work" && zip -q -X -0 case.apk AndroidManifest.xml classes*.dex)

  local -a invocation=("$JAVA" -jar "$FLOWDROID_JAR" -a "$work/case.apk" \
    -p "$ANDROID_PLATFORM" -s "$endpoints" -o "$work/out.xml")
  if [ "$summaries" != "NONE" ]; then
    invocation+=(-tw STUBDROID -t "$summaries")
  fi
  local status=0
  "${invocation[@]}" > "$work/log.txt" 2>&1 || status=$?

  local completion leaks termination results_xml
  completion="$(grep -E 'Found [0-9]+ leaks from [0-9]+ sources' "$work/log.txt" | tail -1 || true)"
  leaks="$(printf '%s' "$completion" | sed -nE 's/.*Found ([0-9]+) leaks.*/\1/p')"
  termination="None"
  results_xml="absent"
  if [ -f "$work/out.xml" ]; then
    results_xml="written"
    termination="\"$(sed -nE 's/.*TerminationState="([^"]+)".*/\1/p' "$work/out.xml" | head -1)\""
  fi
  if grep -q "The data flow analysis has failed" "$work/log.txt"; then
    echo "probe $name: the analyzer reported failure; see $work/log.txt" >&2
    exit 1
  fi
  [ -n "$completion" ] || { echo "probe $name: no completion line" >&2; exit 1; }

  python3 - "$EVIDENCE/flowdroid-$name.json" <<PY
import json, sys
document = {
    "adapter": "flowdroid",
    "evidence_kind": "flowdroid-modeling-probe",
    "case_directory": "cases/taint/java/$case_dir",
    "entry_call": "$entry_call",
    "sources_sinks": "$(basename "$endpoints")",
    "model_configuration": "$model",
    "invocation_shape": "java -jar soot-infoflow-cmd -a case.apk -p android.jar -s <endpoints> -o out.xml"
        + ("" if "$summaries" == "NONE" else " -tw STUBDROID -t <summaries>"),
    "exit_status": $status,
    "completion_line": "$(printf '%s' "$completion" | sed -E 's/.*(Found [0-9]+ leaks from [0-9]+ sources).*/\1/')",
    "leaks_reported": ${leaks:-None},
    "results_xml": "$results_xml",
    "termination_state": $termination,
}
with open(sys.argv[1], "w") as handle:
    json.dump(document, handle, indent=2, sort_keys=True)
    handle.write("\n")
PY
  echo "retained $EVIDENCE/flowdroid-$name.json (leaks: ${leaks:-?})"
}

# The per-case endpoint definitions: the same name-derived signatures the
# runner witnesses from the compiled classes, stated literally here so the
# probe stands alone.
endpoints() {
  local file="$SCRATCH/$1.txt"
  printf '%s\n' "${@:2}" > "$file"
  printf '%s' "$file"
}

# A copy of the committed summaries with one declaration deleted, produced
# with python so the deletion is surgical and auditable.
strip_summary() {
  local out="$SCRATCH/summaries-$1" file="$2" marker="$3"
  rm -rf "$out"; cp -R "$SUMMARIES" "$out"
  python3 - "$out/$file" "$marker" <<'PY'
import re, sys
path, marker = sys.argv[1], sys.argv[2]
text = open(path).read()
pattern = re.compile(
    r'\t\t<method id="' + re.escape(marker) + r'">.*?</method>\n', re.S)
stripped, count = pattern.subn("", text)
assert count == 1, f"expected one {marker} entry in {path}, found {count}"
open(path, "w").write(stripped)
PY
  printf '%s' "$out"
}

# --- Category P: template 3, the opaque propagator ---------------------------
T3_ENDPOINTS_POS="$(endpoints t3-pos \
  '<dataflowbench.taint.ModelOpaquePropagatorPositive: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelOpaquePropagatorPositive: void dfb_sink(java.lang.String)> -> _SINK_')"
run_probe opaque-propagator-with-model model-opaque-propagator-positive \
  'ModelOpaquePropagatorPositive.run()' "$T3_ENDPOINTS_POS" "$SUMMARIES" \
  "committed adapters/flowdroid/summaries/model-java (carry: Parameter 0 -> Return)"
NO_CARRY="$(strip_summary no-carry dataflowbench.taint.Opaque.xml 'java.lang.String carry(java.lang.String)')"
run_probe opaque-propagator-without-model model-opaque-propagator-positive \
  'ModelOpaquePropagatorPositive.run()' "$T3_ENDPOINTS_POS" "$NO_CARRY" \
  "committed summaries with the carry declaration deleted"

# --- Category P: template 4, positional fidelity -----------------------------
T4_POS="$(endpoints t4-pos \
  '<dataflowbench.taint.ModelPropagatorPositionPositive: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelPropagatorPositionPositive: void dfb_sink(java.lang.String)> -> _SINK_')"
T4_NEG="$(endpoints t4-neg \
  '<dataflowbench.taint.ModelPropagatorPositionNegative: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelPropagatorPositionNegative: void dfb_sink(java.lang.String)> -> _SINK_')"
run_probe propagator-position-declared-position model-propagator-position-positive \
  'ModelPropagatorPositionPositive.run()' "$T4_POS" "$SUMMARIES" \
  "committed summaries (select: Parameter 1 -> Return); taint at the declared position 1"
run_probe propagator-position-undeclared-position model-propagator-position-negative \
  'ModelPropagatorPositionNegative.run()' "$T4_NEG" "$SUMMARIES" \
  "committed summaries (select: Parameter 1 -> Return); taint at the undeclared position 0"

# --- Category Z: template 5, the sanitizer kill ------------------------------
T5_NEG="$(endpoints t5-neg \
  '<dataflowbench.taint.ModelSanitizerKillNegative: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelSanitizerKillNegative: void dfb_sink(java.lang.String)> -> _SINK_')"
run_probe sanitizer-kill-with-model model-sanitizer-kill-negative \
  'ModelSanitizerKillNegative.run()' "$T5_NEG" "$SUMMARIES" \
  "committed summaries (scrub: clear on Parameter 0)"
NO_SCRUB="$(strip_summary no-scrub dataflowbench.taint.Clean.xml 'java.lang.String scrub(java.lang.String)')"
run_probe sanitizer-kill-without-model model-sanitizer-kill-negative \
  'ModelSanitizerKillNegative.run()' "$T5_NEG" "$NO_SCRUB" \
  "committed summaries with the scrub declaration deleted"

# --- Category Z: template 6, selectivity is undecidable ----------------------
T6_POS="$(endpoints t6-pos \
  '<dataflowbench.taint.ModelSanitizerSelectivityPositive: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelSanitizerSelectivityPositive: void dfb_sink(java.lang.String)> -> _SINK_')"
run_probe sanitizer-selectivity-undecidable model-sanitizer-selectivity-positive \
  'ModelSanitizerSelectivityPositive.run()' "$T6_POS" "$SUMMARIES" \
  "committed summaries; the flow passes through the UNDECLARED sibling sanitize, and the class-exclusive summary resolution suppresses it anyway"

# --- Category O: template 8, the store-through summary -----------------------
T8_POS="$(endpoints t8-pos \
  '<dataflowbench.taint.ModelSummaryFieldPositive: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelSummaryFieldPositive: void dfb_sink(java.lang.String)> -> _SINK_')"
T8_NEG="$(endpoints t8-neg \
  '<dataflowbench.taint.ModelSummaryFieldNegative: java.lang.String dfb_source()> -> _SOURCE_' \
  '<dataflowbench.taint.ModelSummaryFieldNegative: void dfb_sink(java.lang.String)> -> _SINK_')"
run_probe summary-field-with-model model-summary-field-positive \
  'ModelSummaryFieldPositive.run()' "$T8_POS" "$SUMMARIES" \
  "committed summaries (deposit: Parameter 0 -> Parameter 1 access path .payload); sink reads box.payload"
run_probe summary-field-sibling model-summary-field-negative \
  'ModelSummaryFieldNegative.run()' "$T8_NEG" "$SUMMARIES" \
  "committed summaries; sink reads the sibling field box.spare"
NO_DEPOSIT="$(strip_summary no-deposit dataflowbench.taint.Bridge.xml 'void deposit(java.lang.String,dataflowbench.taint.Box)')"
run_probe summary-field-without-model model-summary-field-positive \
  'ModelSummaryFieldPositive.run()' "$T8_POS" "$NO_DEPOSIT" \
  "committed summaries with the deposit declaration deleted (deposit's body writes nothing)"

# --- Category E: no entry-root declaration surface ---------------------------
E_XML="$SCRATCH/entrypoint-sources-sinks.xml"
cat > "$E_XML" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<sinkSources>
  <category id="NO_CATEGORY">
    <method signature="&lt;dataflowbench.taint.Handler: void onRequest(java.lang.String)&gt;" callType="callback">
      <param index="0">
        <accessPath isSource="true" isSink="false" />
      </param>
    </method>
    <method signature="&lt;dataflowbench.taint.Handler: void dfb_sink(java.lang.String)&gt;">
      <param index="0">
        <accessPath isSource="false" isSink="true" />
      </param>
    </method>
  </category>
</sinkSources>
XML
run_probe entrypoint-parameter-undeclarable model-entrypoint-parameter-positive \
  'new Handler()' "$E_XML" NONE \
  "XML sources-and-sinks definition binding onRequest's parameter 0 as a source; the handler is never called and the manifest-derived entry model creates no root from a declaration"

echo "all FlowDroid modeling probes retained under $EVIDENCE"

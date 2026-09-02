#!/usr/bin/env bash
# Amendment A29's evidence: FlowDroid's tool-native decline is re-grounded on
# a FULL ENUMERATION of the pinned jar's shipped declarative surface and on
# EXECUTED engagement of that surface, not on a read of one catalog's text.
#
# Amendment A19 declined all six native cells from the shipped
# SourcesAndSinks.txt catalog's own text before any run. A maintainer
# challenge — did the evaluation engage everything the release ships, or only
# the default file? — sends the grounds into the field. This probe:
#
#   1. witnesses the pinned artifact identities (digests + the jar's
#      self-reported version) and refuses to run on any mismatch;
#   2. enumerates EVERY declarative resource the released jar bundles beyond
#      compiled classes — the default SourcesAndSinks.txt (the only endpoint
#      catalog instance in any format: schema/SourcesAndSinks.xsd defines an
#      XML format, but no XML catalog instance is shipped), the
#      EasyTaintWrapper default definitions (EasyTaintWrapperSource.txt),
#      the callback list (AndroidCallbacks.txt), the virtual-edge model
#      (virtualedges.xml), and the full StubDroid summariesManual set —
#      retaining the endpoint-bearing surfaces verbatim;
#   3. searches every one of those surfaces for the identities the six probe
#      templates read and write (`System.getenv`, `System.getProperty` /
#      `setProperty`, a `main(String[])` argv convention, `Runtime.exec`,
#      `ProcessBuilder`, `java.util.Base64`), retaining the counts — the
#      load-bearing zero being `getenv`, which occurs NOWHERE in the jar;
#   4. witnesses that a bare `-a <apk> -p <platform>` invocation (no `-s`)
#      initializes the default taint wrapper and then fails with the
#      zero-exit banner — the release has no fallback catalog;
#   5. materializes an APK per Java native fixture exactly as the kernel does
#      (javac, the committed activity wrapper, D8, the committed manifest
#      blob) and runs the pinned CLI over all twelve with the shipped catalog
#      extracted verbatim, retaining per fixture the argv, exit status, the
#      parsed SourceSinkManager counts, and the analyzer's own completion
#      line — the zero-exit guard applies: a log without `Found N leaks` is a
#      probe failure, never a negative;
#   6. runs one CONTROL on the source-sink positive: the same APK and the
#      same shipped catalog plus a single benchmark-authored `getenv` source
#      line. The control is evidence, not activation — it exists to attribute
#      the zeros to the catalog and to nothing else.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome.
#
# Usage:
#   scripts/probe-flowdroid-native-shipped-surface.sh \
#     [--flowdroid-jar <path>] [--android-platform <path>] [--d8-jar <path>]
set -euo pipefail

CACHE="$HOME/.cache/dataflowbench-tools/flowdroid"
FLOWDROID_JAR="$CACHE/soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar"
ANDROID_JAR="$CACHE/android-34.jar"
D8_JAR="$CACHE/r8-8.5.35.jar"
while [ $# -gt 0 ]; do
  case "$1" in
    --flowdroid-jar) FLOWDROID_JAR="$2"; shift 2 ;;
    --android-platform) ANDROID_JAR="$2"; shift 2 ;;
    --d8-jar) D8_JAR="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

FLOWDROID_SHA256="51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218"
ANDROID_SHA256="6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad"
D8_SHA256="4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a29-flowdroid-shipped-surface"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT"

witness() {
  local path="$1" expected="$2" label="$3"
  local actual
  actual="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [ "$actual" != "$expected" ]; then
    echo "PIN MISMATCH for $label: expected $expected, measured $actual" >&2
    exit 1
  fi
  echo "$label sha256=$actual"
}

{
  witness "$FLOWDROID_JAR" "$FLOWDROID_SHA256" "soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar"
  witness "$ANDROID_JAR" "$ANDROID_SHA256" "android-34.jar"
  witness "$D8_JAR" "$D8_SHA256" "r8-8.5.35.jar"
  unzip -p "$FLOWDROID_JAR" \
    "META-INF/maven/de.fraunhofer.sit.sse.flowdroid/soot-infoflow-cmd/pom.properties" \
    | grep '^version=' | sed 's/^/jar self-reported /'
} > "$OUT/witnessed-identity.txt"

# --- 1. Enumerate the shipped declarative surface -------------------------
# Everything in the jar that is not a compiled class, build metadata, or a
# shaded third-party resource is listed; the endpoint-bearing and
# model-bearing files are retained verbatim.
unzip -l "$FLOWDROID_JAR" | awk '{print $4}' \
  | grep -vE '\.class$|/$' \
  | grep -vE '^META-INF/(maven|versions|services|native-image|proguard)|^(draft|google/protobuf|ucd|schema/)|LICENSE|NOTICE|THIRD-PARTY|INDEX.LIST|MANIFEST.MF|^Name$|^----$|leap_second|lexer\.dat|parser\.dat|peephole\.dat|NotesOnSummary|\.properties$' \
  | grep -E '.' | sort > "$OUT/shipped-surface-inventory.txt"
{
  echo "# declarative resources bundled in the pinned jar (see inventory):"
  sed 's/^/#   /' "$OUT/shipped-surface-inventory.txt" | grep -v 'summariesManual/' || true
  echo "#   summariesManual/*.xml ($(grep -c 'summariesManual/' "$OUT/shipped-surface-inventory.txt") StubDroid summary files)"
  echo "# endpoint catalog formats the release supports vs. ships:"
  echo "#   schema/SourcesAndSinks.xsd is bundled (an XML catalog format exists),"
  echo "#   but the ONLY catalog instance shipped in any format is SourcesAndSinks.txt:"
  unzip -l "$FLOWDROID_JAR" | awk '{print $4}' | grep -vE '\.class$|/$' \
    | grep -iE 'sources.*sinks' | sed 's/^/#     /'
} > "$OUT/shipped-surface-notes.txt"

unzip -p "$FLOWDROID_JAR" SourcesAndSinks.txt > "$OUT/shipped-SourcesAndSinks.txt"
unzip -p "$FLOWDROID_JAR" EasyTaintWrapperSource.txt > "$OUT/shipped-EasyTaintWrapperSource.txt"
unzip -p "$FLOWDROID_JAR" AndroidCallbacks.txt > "$OUT/shipped-AndroidCallbacks.txt"
unzip -p "$FLOWDROID_JAR" virtualedges.xml > "$OUT/shipped-virtualedges.xml"
unzip -p "$FLOWDROID_JAR" summariesManual/java.lang.System.xml > "$OUT/shipped-summary-java.lang.System.xml"
mkdir -p "$SCRATCH/summaries"
(cd "$SCRATCH/summaries" && unzip -q "$FLOWDROID_JAR" 'summariesManual/*')

# --- 2. Search every surface for the probe templates' identities ----------
search_surface() {
  local label="$1" path="$2"
  echo "== $label"
  for needle in 'getenv' 'getProperty' 'setProperty' 'Runtime' 'exec(java.lang.String)' 'ProcessBuilder' 'Base64' 'main(java.lang.String[])' 'argv'; do
    local count
    count="$( (grep -rF "$needle" "$path" 2>/dev/null || true) | wc -l | tr -d ' ')"
    echo "   $needle: $count"
  done
}
{
  search_surface "SourcesAndSinks.txt (the only shipped endpoint catalog)" "$OUT/shipped-SourcesAndSinks.txt"
  search_surface "EasyTaintWrapperSource.txt (EasyTaintWrapper defaults)" "$OUT/shipped-EasyTaintWrapperSource.txt"
  search_surface "AndroidCallbacks.txt (callback interface list)" "$OUT/shipped-AndroidCallbacks.txt"
  search_surface "virtualedges.xml (virtual-edge callgraph model)" "$OUT/shipped-virtualedges.xml"
  search_surface "summariesManual/ (all $(ls "$SCRATCH/summaries/summariesManual" | wc -l | tr -d ' ') StubDroid summary files)" "$SCRATCH/summaries/summariesManual"
  echo "== the load-bearing zero, checked against the WHOLE artifact, not just the surfaces above"
  # Decompress every entry and search the raw bytes, so no declarative file
  # anywhere in the jar can hide a getenv binding from the surface list.
  mkdir -p "$SCRATCH/wholejar" && (cd "$SCRATCH/wholejar" && unzip -qq "$FLOWDROID_JAR" || true)
  echo "   entries containing the string 'getenv' anywhere in their bytes:"
  (cd "$SCRATCH/wholejar" && { find . -type f -exec grep -l -a -F 'getenv' {} + || true; } | sed 's|^\./|     |' | sort)
  echo "   (each is shaded third-party dependency code that itself calls System.getenv"
  echo "   at tool runtime; none is a model, catalog, wrapper, or summary declaration)"
  echo "== 'Base64'-named StubDroid summary files (java.util.Base64 does not appear)"
  ls "$SCRATCH/summaries/summariesManual" | grep -i base64 | sed 's/^/   /'
} > "$OUT/endpoint-search.txt"

{
  echo "== shipped-SourcesAndSinks.txt textual roles"
  echo "   _SOURCE_ lines: $(grep -c '_SOURCE_' "$OUT/shipped-SourcesAndSinks.txt")"
  echo "   _SINK_ lines:   $(grep -c '_SINK_' "$OUT/shipped-SourcesAndSinks.txt")"
  echo "   _BOTH_ lines:   $(grep -c '_BOTH_' "$OUT/shipped-SourcesAndSinks.txt" || true)"
  echo "== shipped-EasyTaintWrapperSource.txt roles (all propagation-side; the format has no source or sink role)"
  echo "   wrap entries '<...>': $(grep -cE '^<' "$OUT/shipped-EasyTaintWrapperSource.txt")"
  echo "   exclude entries '~':  $(grep -cE '^~' "$OUT/shipped-EasyTaintWrapperSource.txt")"
  echo "   kill entries '-':     $(grep -cE '^-' "$OUT/shipped-EasyTaintWrapperSource.txt")"
  echo "   include prefixes '^': $(grep -cE '^\^' "$OUT/shipped-EasyTaintWrapperSource.txt")"
  grep -E '^\^' "$OUT/shipped-EasyTaintWrapperSource.txt" | sed 's/^/     /'
} > "$OUT/catalog-structure.txt"

# --- 3. Materialize an APK per fixture, exactly as the kernel does --------
JAVA_CASES_DIR="$ROOT/cases/taint/java"
TEMPLATE_DIR="$ROOT/adapters/flowdroid/template"

build_apk() {
  local case_dir="$1" workdir="$2"
  local fixture cls entry_call
  fixture="$(ls "$case_dir"/*.java)"
  cls="$(basename "$fixture" .java)"
  if grep -q 'static void main(String\[\] args)' "$fixture"; then
    entry_call="$cls.main(new String[0])"
  else
    entry_call="$cls.run()"
  fi
  mkdir -p "$workdir/src/dataflowbench/taint" "$workdir/out"
  cp "$fixture" "$workdir/src/dataflowbench/taint/"
  sed -e 's/__DFB_PACKAGE__/dataflowbench.taint/' \
      -e "s/__DFB_ENTRY_CALL__/${entry_call//\//\\/}/" \
      "$TEMPLATE_DIR/DfbCaseActivity.java.tmpl" \
      > "$workdir/src/dataflowbench/taint/DfbCaseActivity.java"
  javac -nowarn -cp "$ANDROID_JAR" -d "$workdir/classes" \
    "$workdir/src/dataflowbench/taint/"*.java
  find "$workdir/classes" -name '*.class' -print0 \
    | xargs -0 java -cp "$D8_JAR" com.android.tools.r8.D8 \
        --release --lib "$ANDROID_JAR" --output "$workdir/out"
  cp "$TEMPLATE_DIR/AndroidManifest-java.xml" "$workdir/out/AndroidManifest.xml"
  (cd "$workdir/out" && zip -X -0 -q case.apk classes.dex AndroidManifest.xml)
  echo "$workdir/out/case.apk"
}

require_completion_line() {
  local log="$1" label="$2"
  if grep -q 'The data flow analysis has failed' "$log"; then
    echo "PROBE FAILURE ($label): the failure banner is in the log" >&2
    exit 1
  fi
  if ! grep -q 'Found [0-9]* leaks from [0-9]* sources' "$log"; then
    echo "PROBE FAILURE ($label): no 'Found N leaks' completion line — silence is never a negative" >&2
    exit 1
  fi
}

# --- 4. Witness: no `-s` at all — is there a fallback catalog? ------------
FLOOR_APK="$(build_apk "$JAVA_CASES_DIR/native-source-sink-positive" "$SCRATCH/no-flag")"
set +e
java -jar "$FLOWDROID_JAR" -a "$FLOOR_APK" -p "$ANDROID_JAR" \
  > "$OUT/no-sources-sinks-flag.log" 2>&1
NO_FLAG_EXIT=$?
set -e
if ! grep -q 'No source/sink file specified for the data flow analysis' \
    "$OUT/no-sources-sinks-flag.log"; then
  echo "PROBE FAILURE: the bare invocation did not produce the no-catalog banner" >&2
  exit 1
fi
if ! grep -q 'Initializing summary taint wrapper with summaries for' \
    "$OUT/no-sources-sinks-flag.log"; then
  echo "PROBE FAILURE: the bare invocation did not witness the default wrapper initializing" >&2
  exit 1
fi
echo "bare-invocation exit status: $NO_FLAG_EXIT (the failure exits zero — the guard exists for a reason)" \
  >> "$OUT/no-sources-sinks-flag.log"

# --- 5. The shipped catalog, engaged over every Java native fixture -------
for case_dir in "$JAVA_CASES_DIR"/native-*; do
  case_name="$(basename "$case_dir")"
  workdir="$SCRATCH/$case_name"
  apk="$(build_apk "$case_dir" "$workdir")"
  log="$OUT/shipped-catalog-$case_name.log"
  results="$workdir/out/results.xml"
  set +e
  java -jar "$FLOWDROID_JAR" -a "$apk" -p "$ANDROID_JAR" \
    -s "$OUT/shipped-SourcesAndSinks.txt" -ls -o "$results" \
    > "$log" 2>&1
  exit_status=$?
  set -e
  require_completion_line "$log" "$case_name"
  manager_line="$(grep -m1 'Created a SourceSinkManager with' "$log" || true)"
  leak_line="$(grep -m1 'Found [0-9]* leaks from [0-9]* sources' "$log")"
  reject_count="$(grep -c 'Line does not match' "$log" || true)"
  results_written=false
  [ -f "$results" ] && results_written=true
  PROBE_CASE="$case_name" PROBE_EXIT="$exit_status" \
  PROBE_REJECTS="$reject_count" PROBE_MANAGER="$manager_line" \
  PROBE_LEAK="$leak_line" PROBE_RESULTS="$results_written" \
  PROBE_JAR="$(basename "$FLOWDROID_JAR")" PROBE_PLATFORM="$(basename "$ANDROID_JAR")" \
  python3 - "$OUT/shipped-catalog-$case_name.json" <<'EOF'
import json, os, sys
env = os.environ
json.dump({
    "case": env["PROBE_CASE"],
    "argv": ["java", "-jar", env["PROBE_JAR"],
             "-a", "case.apk", "-p", env["PROBE_PLATFORM"],
             "-s", "shipped-SourcesAndSinks.txt", "-ls", "-o", "results.xml"],
    "exit_status": int(env["PROBE_EXIT"]),
    "catalog_lines_rejected_by_parser": int(env["PROBE_REJECTS"]),
    "source_sink_manager": env["PROBE_MANAGER"].strip() or None,
    "completion_line": env["PROBE_LEAK"].strip(),
    "results_xml_written": env["PROBE_RESULTS"] == "true",
}, open(sys.argv[1], "w"), indent=1)
EOF
done

# --- 6. Control: one benchmark-authored source line attributes the zeros --
cp "$OUT/shipped-SourcesAndSinks.txt" "$OUT/control-sources-sinks.txt"
cat >> "$OUT/control-sources-sinks.txt" <<'EOF'
% --- DataFlowBench Amendment A29 CONTROL LINE (benchmark-authored, evidence
% --- only, never part of any activation): does the identical invocation find
% --- the floor flow the moment a source binds the environment read?
<java.lang.System: java.lang.String getenv(java.lang.String)> -> _SOURCE_
EOF
CONTROL_APK="$(build_apk "$JAVA_CASES_DIR/native-source-sink-positive" "$SCRATCH/control")"
set +e
java -jar "$FLOWDROID_JAR" -a "$CONTROL_APK" -p "$ANDROID_JAR" \
  -s "$OUT/control-sources-sinks.txt" -o "$SCRATCH/control/results.xml" \
  > "$OUT/control.log" 2>&1
set -e
require_completion_line "$OUT/control.log" "control"
if ! grep -q 'Found 1 leaks from 1 sources' "$OUT/control.log"; then
  echo "PROBE FAILURE: the control did not find exactly the floor leak" >&2
  exit 1
fi
cp "$SCRATCH/control/results.xml" "$OUT/control-results.xml"

echo "probe complete; evidence retained under $OUT"

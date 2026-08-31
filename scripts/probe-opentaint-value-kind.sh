#!/usr/bin/env bash
# The OpenTaint value-kind probe: the discrimination behind the adapter
# README's statement that the pinned engine carries taint on reference-typed
# values and drops it on numeric ones.
#
# The Java and Kotlin core kernels encode their endpoint contracts with `int`
# (`Int`) returns in most templates, so an OpenTaint miss on such a case is
# ambiguous on its own: it could be the semantic dimension under test, or it
# could be the value's type. This probe removes the ambiguity by holding the
# flow shape constant — one direct assignment from a nullary source into a
# single-argument sink, the simplest shape in the corpus — and varying only
# the value type across four variants:
#
#   1. `String`  source/sink  — the reference baseline
#   2. `Object`  source/sink  — reference, no string semantics
#   3. `int`     source/sink  — the kernels' majority encoding
#   4. `Integer` source/sink  — the same value boxed
#
# On the pinned analyzer the two reference variants are reported and the two
# numeric variants are not, under one rule file whose four rules load
# identically (the retained load trace shows all four registered). That is the
# evidence that the kernels' numeric false negatives measure a value-kind
# boundary of the engine, not the templates' semantic dimensions — and it is
# retained as a probe, never as a partition input: the scored population is
# unchanged by it, per the adapter contract's ban on observation-derived
# partitions.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome. Raw outputs land in
# reports/raw/opentaint-value-kind-probe/.
#
# Usage:
#   scripts/probe-opentaint-value-kind.sh \
#     --analyzer-jar <opentaint-project-analyzer.jar> [--java java] [--javac javac]
set -euo pipefail

JAVA=java
JAVAC=javac
ANALYZER=""
while [ $# -gt 0 ]; do
  case "$1" in
    --analyzer-jar) ANALYZER="$2"; shift 2 ;;
    --java) JAVA="$2"; shift 2 ;;
    --javac) JAVAC="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
if [ -z "$ANALYZER" ]; then
  echo "--analyzer-jar is required" >&2
  exit 2
fi

EXPECTED_SHA256=811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54
ACTUAL_SHA256=$(shasum -a 256 "$ANALYZER" | cut -d' ' -f1)
if [ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]; then
  echo "analyzer jar sha256 $ACTUAL_SHA256 is not the pinned $EXPECTED_SHA256" >&2
  exit 2
fi

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/reports/raw/opentaint-value-kind-probe"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$OUT" "$WORK/source/probe" "$WORK/classes" "$WORK/out"

cat > "$WORK/source/probe/ValueKindProbe.java" <<'EOF'
package probe;

final class ValueKindProbe {
    static String string_src() { return "tainted"; }
    static void string_sink(String value) { }
    static void runString() { string_sink(string_src()); }

    static Object object_src() { return new Object(); }
    static void object_sink(Object value) { }
    static void runObject() { object_sink(object_src()); }

    static int int_src() { return 1; }
    static void int_sink(int value) { }
    static void runInt() { int_sink(int_src()); }

    static Integer boxed_src() { return 1; }
    static void boxed_sink(Integer value) { }
    static void runBoxed() { boxed_sink(boxed_src()); }
}
EOF

cat > "$WORK/rule.yaml" <<'EOF'
rules:
EOF
for KIND in string object int boxed; do
  cat >> "$WORK/rule.yaml" <<EOF
  - id: value-kind-$KIND
    severity: ERROR
    message: value-kind probe ($KIND)
    languages: [java]
    mode: taint
    pattern-sources:
      - pattern: ${KIND}_src()
    pattern-sinks:
      - patterns:
          - pattern: ${KIND}_sink(\$DFBVAL);
          - focus-metavariable: \$DFBVAL
EOF
done

"$JAVAC" -nowarn -d "$WORK/classes" "$WORK/source/probe/ValueKindProbe.java"

cat > "$WORK/project.yaml" <<EOF
javaProjects:
  - sourceRoot: $WORK/source
    modules:
      - moduleSourceRoot: $WORK/source
        packages:
          - probe
        moduleClasses:
          - $WORK/classes
EOF

"$JAVA" -jar "$ANALYZER" \
  --project="$WORK/project.yaml" \
  --project-kind=unknown \
  "--debug-run-analysis-on-selected-entry-points=*" \
  --semgrep-rule-set="$WORK/rule.yaml" \
  --semgrep-rule-load-trace="$WORK/out/load-trace.json" \
  --output-dir="$WORK/out" >/dev/null

cp "$WORK/source/probe/ValueKindProbe.java" "$OUT/ValueKindProbe.java"
cp "$WORK/rule.yaml" "$OUT/rule.yaml"
cp "$WORK/out/load-trace.json" "$OUT/load-trace.json"
cp "$WORK/out/report-ifds.sarif" "$OUT/report-ifds.sarif"

echo "retained probe evidence in reports/raw/opentaint-value-kind-probe/"
echo "rules that produced a finding:"
python3 - "$OUT/report-ifds.sarif" <<'EOF'
import json, sys
sarif = json.load(open(sys.argv[1]))
found = sorted({r["ruleId"] for run in sarif["runs"] for r in run["results"]})
for rule in found:
    print(f"  {rule}")
if not found:
    print("  (none)")
EOF

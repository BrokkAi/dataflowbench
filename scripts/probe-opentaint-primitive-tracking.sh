#!/usr/bin/env bash
# The OpenTaint primitive-tracking probe: the evidence behind Amendment A11
# (docs/adapters.md#amendments).
#
# The value-kind probe (probe-opentaint-value-kind.sh) measured the pinned
# engine dropping taint on `int` and boxed `Integer` under the adapter's rule
# templates, and the adapter published that as an engine boundary. Upstream's
# response to the report (seqra/opentaint#388) identified it as a *default
# rule configuration* instead: primitive tracking is disabled by default and
# enabled per rule with `options: primitive-tracking: true`.
#
# This probe measures that claim on the same pinned jar, holding the
# value-kind probe's fixture shape and invocation constant and varying only
# the rule option. It runs the analyzer twice over one fixture:
#
#   baseline/ - the four value-kind rules exactly as before (option absent)
#   enabled/  - the same four rules with `primitive-tracking: true`
#
# and the fixture extends each value kind (String, Object, int, Integer) with
# two negative arms so the option's over-approximation cost is measured, not
# assumed:
#
#   run<Kind>Clean     - an untainted same-type value reaches the sink
#   run<Kind>Overwrite - the tainted value is overwritten before the sink
#
# Measured on the pinned analyzer: the baseline run reproduces the value-kind
# probe (String and Object report, neither numeric variant does), and the
# enabled run reports all four positive arms - `int` and boxed `Integer`
# carry - with no finding on any clean or overwrite arm. Like the value-kind
# probe, this is retained as evidence and is never a partition input: the
# scored population is unchanged by it.
#
# Raw outputs land in reports/raw/opentaint-primitive-tracking-probe/.
#
# Usage:
#   scripts/probe-opentaint-primitive-tracking.sh \
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
OUT="$ROOT/reports/raw/opentaint-primitive-tracking-probe"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT" "$WORK/source/probe" "$WORK/classes"

cat > "$WORK/source/probe/PrimitiveTrackingProbe.java" <<'EOF'
package probe;

final class PrimitiveTrackingProbe {
    static String string_src() { return "tainted"; }
    static String string_other() { return "clean"; }
    static void string_sink(String value) { }
    static void runString() { string_sink(string_src()); }
    static void runStringClean() { string_sink(string_other()); }
    static void runStringOverwrite() { String v = string_src(); v = "clean"; string_sink(v); }

    static Object object_src() { return new Object(); }
    static Object object_other() { return new Object(); }
    static void object_sink(Object value) { }
    static void runObject() { object_sink(object_src()); }
    static void runObjectClean() { object_sink(object_other()); }
    static void runObjectOverwrite() { Object v = object_src(); v = new Object(); object_sink(v); }

    static int int_src() { return 1; }
    static int int_other() { return 2; }
    static void int_sink(int value) { }
    static void runInt() { int_sink(int_src()); }
    static void runIntClean() { int_sink(int_other()); }
    static void runIntOverwrite() { int v = int_src(); v = 0; int_sink(v); }

    static Integer boxed_src() { return 1; }
    static Integer boxed_other() { return 2; }
    static void boxed_sink(Integer value) { }
    static void runBoxed() { boxed_sink(boxed_src()); }
    static void runBoxedClean() { boxed_sink(boxed_other()); }
    static void runBoxedOverwrite() { Integer v = boxed_src(); v = 0; boxed_sink(v); }
}
EOF

# $1 = rule file; $2 = "yes" to add `options: primitive-tracking: true`.
write_rules() {
  echo "rules:" > "$1"
  for KIND in string object int boxed; do
    cat >> "$1" <<EOF
  - id: value-kind-$KIND
    severity: ERROR
    message: primitive-tracking probe ($KIND)
    languages: [java]
    mode: taint
EOF
    if [ "$2" = yes ]; then
      cat >> "$1" <<EOF
    options:
      primitive-tracking: true
EOF
    fi
    cat >> "$1" <<EOF
    pattern-sources:
      - pattern: ${KIND}_src()
    pattern-sinks:
      - patterns:
          - pattern: ${KIND}_sink(\$DFBVAL);
          - focus-metavariable: \$DFBVAL
EOF
  done
}

"$JAVAC" -nowarn -d "$WORK/classes" "$WORK/source/probe/PrimitiveTrackingProbe.java"

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

for RUN in baseline enabled; do
  if [ "$RUN" = enabled ]; then ENABLE=yes; else ENABLE=no; fi
  mkdir -p "$OUT/$RUN" "$WORK/out-$RUN"
  write_rules "$WORK/rule-$RUN.yaml" "$ENABLE"
  "$JAVA" -jar "$ANALYZER" \
    --project="$WORK/project.yaml" \
    --project-kind=unknown \
    "--debug-run-analysis-on-selected-entry-points=*" \
    --semgrep-rule-set="$WORK/rule-$RUN.yaml" \
    --semgrep-rule-load-trace="$WORK/out-$RUN/load-trace.json" \
    --output-dir="$WORK/out-$RUN" >/dev/null
  cp "$WORK/rule-$RUN.yaml" "$OUT/$RUN/rule.yaml"
  cp "$WORK/out-$RUN/load-trace.json" "$OUT/$RUN/load-trace.json"
  cp "$WORK/out-$RUN/report-ifds.sarif" "$OUT/$RUN/report-ifds.sarif"
done
cp "$WORK/source/probe/PrimitiveTrackingProbe.java" "$OUT/PrimitiveTrackingProbe.java"

echo "retained probe evidence in reports/raw/opentaint-primitive-tracking-probe/"
python3 - "$OUT" <<'EOF'
import json, os, sys
out = sys.argv[1]
src = open(os.path.join(out, "PrimitiveTrackingProbe.java")).read().splitlines()
def arm(line):
    for i in range(line - 1, -1, -1):
        if " run" in src[i] and "(" in src[i]:
            return src[i].split("void ")[-1].split("(")[0]
    return f"line {line}"
for run in ("baseline", "enabled"):
    sarif = json.load(open(os.path.join(out, run, "report-ifds.sarif")))
    rows = sorted({(r["ruleId"],
                    r["locations"][0]["physicalLocation"]["region"]["startLine"])
                   for s in sarif["runs"] for r in s["results"]})
    print(f"{run}: rules that produced a finding:")
    if not rows:
        print("  (none)")
    for rule, line in rows:
        print(f"  {rule} -> {arm(line)}")
EOF

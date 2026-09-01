#!/usr/bin/env bash
# The OpenTaint modeling-surface probe: the field evaluation behind Amendment
# A22's per-category partition row for OpenTaint in docs/modeling-matrix.md.
#
# The pinned analyzer is driven over the *committed Java modeling fixtures*
# with hand-written Semgrep-syntax declarations, one probe arm per question the
# partition has to answer, before any scored modeling run exists. Every arm
# retains its rule, its rule-load trace, and its verbatim SARIF, so each
# declined category's rationale points at bytes rather than at a reading of
# the documentation.
#
# What each arm establishes (categories per docs/modeling-matrix.md):
#
#   S  s-source-*, s-sink-*          declared source/sink activation and
#                                    identity binding (fetchLocal/discard are
#                                    undeclared and stay silent)
#   P  p-unmodeled-positive          load-bearing baseline: with no propagator
#                                    declared, the reflective `Opaque.carry`
#                                    body carries nothing — the engine has no
#                                    optimistic unmodeled-call default
#      p-opaque-*, p-position-*      the assignment-shaped propagator
#                                    (`$TO = Opaque.carry($FROM)`) activates
#                                    arg->return over the lifted JVM IR, and
#                                    positional binding excludes the
#                                    undeclared position
#   Z  z-kill-*, z-selectivity-*     sanitizer activation, selectivity by
#                                    declared identity
#      z-kill-negative-unmodeled     removing the declaration restores the
#                                    flow: the sanitizer is load-bearing
#   O  o-through-*-endpoints-only    with *no* summary declared the engine
#                                    reads both identity bodies and reports
#                                    both cells: the body-reading default
#                                    decides template 7, so no summary can be
#                                    load-bearing
#      o-field-*                     both available encodings of template 8's
#                                    store-through summary (side-effect
#                                    propagator onto the box, and the plain
#                                    form) produce no flow, and the
#                                    `out: 1.payload` field destination has no
#                                    spelling in the from/to vocabulary
#   E  e-sink-only-control           a taint rule whose source matches nothing
#                                    produces nothing (the control both E arms
#                                    are read against)
#      e-def-pattern-*,              method-definition-shaped pattern-sources
#      e-inside-pattern-*            are silently dropped by the rule loader
#                                    (rule generation count falls) and the
#                                    rule degenerates to sink-existence
#                                    matches: both cells are flagged at
#                                    constant-argument callsites, so no
#                                    entry-point declaration is expressible
#   B  b-roundtrip-endpoints-only    no default links the store write to the
#                                    read (empty bodies, no flow)
#      b-roundtrip-static,           neither the static-store nor the
#      b-separation-*                instance-store propagator encoding closes
#                                    the roundtrip, and the surface has no
#                                    store/key vocabulary at all
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome. It is evidence for a preregistered
# partition decision, not a partition input taken from a scored result. Raw
# outputs land in reports/raw/opentaint-modeling-surface-probe/.
#
# Usage:
#   scripts/probe-opentaint-modeling-surface.sh \
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
OUT="$ROOT/reports/raw/opentaint-modeling-surface-probe"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT"

MODELS="$WORK/models"
mkdir -p "$MODELS"
tar xzf "$MODELS_ARCHIVE" -C "$MODELS"

# The shared endpoint declarations every arm carries: the benchmark's own
# canonical `dfb_source`/`dfb_sink`, in the two callsite spellings the lifted
# JVM IR produces (see adapters/opentaint/rules/kernel-java.yaml).
CANONICAL_SOURCES='      - pattern-either:
          - pattern: dfb_source()
          - pattern: $DFBRECV.dfb_source()'
CANONICAL_SINKS='      - patterns:
          - pattern-either:
              - pattern: dfb_sink($DFBVAL);
              - pattern: $DFBSINKRECV.dfb_sink($DFBVAL);
          - focus-metavariable: $DFBVAL'

# rule <file> <sources-block> <sinks-block> [extra-section-block]
write_rule() {
  local file="$1" sources="$2" sinks="$3" extra="${4-}"
  {
    echo "rules:"
    echo "  - id: probe-opentaint-modeling"
    echo "    severity: ERROR"
    echo "    message: OpenTaint modeling-surface probe"
    echo "    languages: [java]"
    echo "    mode: taint"
    echo "    options:"
    echo "      primitive-tracking: true"
    echo "    pattern-sources:"
    echo "$sources"
    if [ -n "$extra" ]; then echo "$extra"; fi
    echo "    pattern-sinks:"
    echo "$sinks"
  } > "$file"
}

# arm <name> <case-directory> <rule-file>
arm() {
  local name="$1" fixture_dir="$ROOT/cases/taint/java/$2" rule="$3"
  local ws="$WORK/ws-$name"
  mkdir -p "$ws/source/dataflowbench/taint" "$ws/classes" "$ws/out" "$OUT/$name"
  cp "$fixture_dir"/*.java "$ws/source/dataflowbench/taint/"
  "$JAVAC" -nowarn -d "$ws/classes" "$ws"/source/dataflowbench/taint/*.java
  cat > "$ws/project.yaml" <<EOF
javaProjects:
  - sourceRoot: $ws/source
    modules:
      - moduleSourceRoot: $ws/source
        packages:
          - dataflowbench.taint
        moduleClasses:
          - $ws/classes
EOF
  "$JAVA" -jar "$ANALYZER" \
    --project="$ws/project.yaml" \
    --project-kind=unknown \
    "--debug-run-analysis-on-selected-entry-points=*" \
    --semgrep-rule-set="$rule" \
    --semgrep-rule-load-trace="$ws/out/load-trace.json" \
    --passthrough-approximations="$MODELS/java/accumulated-fields.yaml" \
    --passthrough-approximations="$MODELS/java/config" \
    --java-dataflow-approximations="$MODELS/java/dataflow/build/classes/java/main" \
    --output-dir="$ws/out" >/dev/null
  cp "$rule" "$OUT/$name/rule.yaml"
  cp "$ws/out/load-trace.json" "$OUT/$name/load-trace.json"
  cp "$ws/out/report-ifds.sarif" "$OUT/$name/report-ifds.sarif"
}

# --- Category S -------------------------------------------------------------
write_rule "$WORK/rule-s-source.yaml" "$CANONICAL_SOURCES
      - pattern: Config.fetchRemote()" "$CANONICAL_SINKS"
arm s-source-positive model-declared-source-positive "$WORK/rule-s-source.yaml"
arm s-source-negative model-declared-source-negative "$WORK/rule-s-source.yaml"

write_rule "$WORK/rule-s-sink.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS
      - patterns:
          - pattern: Audit.record(\$DFBVAL);
          - focus-metavariable: \$DFBVAL"
arm s-sink-positive model-declared-sink-positive "$WORK/rule-s-sink.yaml"
arm s-sink-negative model-declared-sink-negative "$WORK/rule-s-sink.yaml"

# --- Category P -------------------------------------------------------------
# The load-bearing baseline: endpoints only, no propagator.
write_rule "$WORK/rule-endpoints.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS"
arm p-unmodeled-positive model-opaque-propagator-positive "$WORK/rule-endpoints.yaml"

write_rule "$WORK/rule-p-opaque.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-propagators:
      - pattern: $DFBTO = Opaque.carry($DFBFROM)
        from: $DFBFROM
        to: $DFBTO'
arm p-opaque-positive model-opaque-propagator-positive "$WORK/rule-p-opaque.yaml"
arm p-opaque-negative model-opaque-propagator-negative "$WORK/rule-p-opaque.yaml"

write_rule "$WORK/rule-p-position.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-propagators:
      - pattern: $DFBTO = Opaque.select($DFBIGNORED, $DFBFROM)
        from: $DFBFROM
        to: $DFBTO'
arm p-position-positive model-propagator-position-positive "$WORK/rule-p-position.yaml"
arm p-position-negative model-propagator-position-negative "$WORK/rule-p-position.yaml"

# --- Category Z -------------------------------------------------------------
write_rule "$WORK/rule-z.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-sanitizers:
      - pattern: Clean.scrub($DFBCLEANED)'
arm z-kill-positive model-sanitizer-kill-positive "$WORK/rule-z.yaml"
arm z-kill-negative model-sanitizer-kill-negative "$WORK/rule-z.yaml"
arm z-selectivity-positive model-sanitizer-selectivity-positive "$WORK/rule-z.yaml"
arm z-selectivity-negative model-sanitizer-selectivity-negative "$WORK/rule-z.yaml"
# Removing the declaration restores the flow: the sanitizer is load-bearing.
arm z-kill-negative-unmodeled model-sanitizer-kill-negative "$WORK/rule-endpoints.yaml"

# --- Category O -------------------------------------------------------------
# Template 7: with no summary declared at all, the engine reads both identity
# bodies and reports both cells — the body-reading default decides the
# template, which is precisely what the load-bearing-model requirement
# forbids scoring.
arm o-through-positive-endpoints-only model-summary-through-positive "$WORK/rule-endpoints.yaml"
arm o-through-negative-endpoints-only model-summary-through-negative "$WORK/rule-endpoints.yaml"
# Template 8: the two available spellings of a store-through summary. Neither
# produces a flow, and neither can name the `out: 1.payload` field
# destination — `to:` reaches a whole metavariable or nothing.
write_rule "$WORK/rule-o-field-side-effect.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-propagators:
      - pattern: Bridge.deposit($DFBFROM, $DFBTO)
        from: $DFBFROM
        to: $DFBTO
        by-side-effect: true'
arm o-field-positive-side-effect model-summary-field-positive "$WORK/rule-o-field-side-effect.yaml"
arm o-field-negative-side-effect model-summary-field-negative "$WORK/rule-o-field-side-effect.yaml"
write_rule "$WORK/rule-o-field-plain.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-propagators:
      - pattern: Bridge.deposit($DFBFROM, $DFBTO)
        from: $DFBFROM
        to: $DFBTO'
arm o-field-positive-plain model-summary-field-positive "$WORK/rule-o-field-plain.yaml"

# --- Category E -------------------------------------------------------------
# Control: a taint rule whose one source matches nothing produces nothing, so
# the degeneration the next four arms retain is attributable to the dropped
# definition-shaped source and not to the rule shape.
write_rule "$WORK/rule-e-control.yaml" \
'      - pattern: dfb_probe_function_that_does_not_exist()' "$CANONICAL_SINKS"
arm e-sink-only-control model-entrypoint-parameter-positive "$WORK/rule-e-control.yaml"

write_rule "$WORK/rule-e-def.yaml" \
'      - patterns:
          - pattern: |
              void onRequest(String $DFBP) { ... }
          - focus-metavariable: $DFBP' "$CANONICAL_SINKS"
arm e-def-pattern-positive model-entrypoint-parameter-positive "$WORK/rule-e-def.yaml"
arm e-def-pattern-negative model-entrypoint-parameter-negative "$WORK/rule-e-def.yaml"

write_rule "$WORK/rule-e-inside.yaml" \
'      - patterns:
          - pattern-inside: |
              void onRequest(String $DFBP) { ... }
          - pattern: $DFBP' "$CANONICAL_SINKS"
arm e-inside-pattern-positive model-entrypoint-parameter-positive "$WORK/rule-e-inside.yaml"
arm e-inside-pattern-negative model-entrypoint-parameter-negative "$WORK/rule-e-inside.yaml"

# --- Category B -------------------------------------------------------------
arm b-roundtrip-endpoints-only model-store-roundtrip-positive "$WORK/rule-endpoints.yaml"
write_rule "$WORK/rule-b-static.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-propagators:
      - pattern: Store.put($DFBKEY, $DFBFROM)
        from: $DFBFROM
        to: $DFBKEY
        by-side-effect: true
      - pattern: $DFBTO = Store.get($DFBKEY)
        from: $DFBKEY
        to: $DFBTO'
arm b-roundtrip-static model-store-roundtrip-positive "$WORK/rule-b-static.yaml"
write_rule "$WORK/rule-b-instance.yaml" "$CANONICAL_SOURCES" "$CANONICAL_SINKS" \
'    pattern-propagators:
      - pattern: $DFBSTORE.put($DFBKEY, $DFBFROM)
        from: $DFBFROM
        to: $DFBSTORE
        by-side-effect: true
      - pattern: $DFBTO = $DFBSTORE.get($DFBKEY)
        from: $DFBSTORE
        to: $DFBTO'
arm b-separation-positive model-store-separation-positive "$WORK/rule-b-instance.yaml"
arm b-separation-negative model-store-separation-negative "$WORK/rule-b-instance.yaml"

echo "retained probe evidence in reports/raw/opentaint-modeling-surface-probe/"
python3 - "$OUT" <<'EOF'
import json, os, sys
out = sys.argv[1]
for name in sorted(os.listdir(out)):
    sarif = json.load(open(os.path.join(out, name, "report-ifds.sarif")))
    rows = sorted({(r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
                    r["locations"][0]["physicalLocation"]["region"]["startLine"])
                   for run in sarif["runs"] for r in run.get("results", [])})
    if rows:
        where = ", ".join(f"{uri.rsplit('/', 1)[-1]}:{line}" for uri, line in rows)
        print(f"{name}: {len(rows)} finding(s) at {where}")
    else:
        print(f"{name}: no findings")
EOF

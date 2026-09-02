#!/usr/bin/env bash
# Amendment A26's evidence: Joern's tool-native decline is re-grounded on a
# FIELD EVALUATION of the shipped scan product, not on an unpinnability claim.
#
# The preregistered row declined partly on "`joern-scan` exists in the
# distribution but its query database is not shipped: it downloads
# `querydb.zip` from a floating `latest` release asset, unpinnable at run
# time". A maintainer challenge — Joern ships a query database
# (https://queries.joern.io, the joern-scan bundle) — forced the claim into
# the field, where half of it failed: the pinned release publishes a
# **versioned** `querydb.zip` asset, and the shipped
# `joern-scan --updatedb --dbversion <pin>` installs exactly that asset. The
# bundle is pinnable, and the product runs with zero benchmark input.
#
# What survives, measured rather than asserted, is the decline itself. This
# probe installs the version-pinned bundle into a COPY of the pinned
# distribution (the pin is never mutated), enumerates every query it ships,
# scans all thirty-six tool-native probe fixtures (twelve per language), and
# retains, per fixture, the exact argv, the exit status, and the count of
# emitted findings. It also retains the one binding check that explains the
# Java column: the bundle's only query naming this profile's command sink —
# `call-to-exec`, `cpg.method("java.lang.Runtime.exec").callIn` — filters the
# method NAME property with a full-match regex, and a javasrc2cpg method's
# name is `exec`, so the query matches zero methods on the very graph whose
# `cpg.method("exec").callIn` is non-empty.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome.
#
# Usage:
#   scripts/probe-joern-scan-native.sh [--joern-dist <path>] [--dbversion <v>]
set -euo pipefail

JOERN_DIST="$HOME/Workspace/joernio/joern-v4.0.614/joern-cli"
DBVERSION="4.0.614"
while [ $# -gt 0 ]; do
  case "$1" in
    --joern-dist) JOERN_DIST="$2"; shift 2 ;;
    --dbversion) DBVERSION="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a26-joern-scan-native"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT"

# The pin is never mutated: the probe works on a copy, so installing the
# query bundle cannot change what any kernel or native run sees.
cp -R "$JOERN_DIST" "$SCRATCH/joern-dist"
DIST="$SCRATCH/joern-dist"

scan() {
  # Call the bin script directly: the top-level wrapper discards stderr into
  # /tmp/joern-scan-log.txt, and a swallowed crash is exactly what this probe
  # exists to rule out.
  "$DIST/bin/joern-scan" \
    -Dlog4j.configurationFile="$DIST/conf/log4j2.xml" "$@"
}

scan --help 2>/dev/null | grep '^Version:' > "$OUT/witnessed-version.txt"

# The versioned release asset the shipped updater resolves for this pin, with
# its digest: the floating `latest` URL is still in the binary, but
# `--dbversion` selects this one, which is what makes the bundle pinnable.
QUERYDB_URL="https://github.com/joernio/joern/releases/download/v${DBVERSION}/querydb.zip"
curl -sfL -o "$SCRATCH/querydb.zip" "$QUERYDB_URL"
{
  echo "url: $QUERYDB_URL"
  echo "sha256: $(shasum -a 256 "$SCRATCH/querydb.zip" | cut -d' ' -f1)"
} > "$OUT/querydb-zip-provenance.txt"

# Install through the shipped updater itself — the product's own path, aimed
# at the version-pinned asset rather than `latest`.
scan --updatedb --dbversion "$DBVERSION" > "$OUT/updatedb.log" 2>&1

scan --list-query-names 2>/dev/null > "$OUT/query-names.txt"
scan --dump-to "$OUT/querydb.json" > /dev/null 2>&1

summarize() {
  python3 - "$1" "$2" "$3" "$4" "$OUT" <<'PY'
import json, re, sys
fixture, language, argv_json, status, out = sys.argv[1:6]
text = open(f"{out}/scan-{language}-{fixture}.txt", encoding="utf-8", errors="replace").read()
results = re.findall(r"^Result: .*$", text, re.M)
summary = {
    "probe": fixture,
    "language": language,
    "invocation": json.loads(argv_json),
    "scan_exit_status": int(status),
    "scan_pass_completed": "Pass io.joern.console.scan.ScanPass completed" in text,
    "result_count": len(results),
    "results": results,
    "evidence_kind": "retained-scan-bundle-probe",
}
with open(f"{out}/scan-{language}-{fixture}.json", "w") as fh:
    json.dump(summary, fh, indent=2)
    fh.write("\n")
print(f"{language}/{fixture}: results={len(results)}")
PY
}

for language in java javascript python; do
  # A scan writes a `workspace/` directory under the CWD; each language gets
  # its own so same-named fixtures cannot collide.
  run_dir="$SCRATCH/run-$language"
  mkdir -p "$run_dir"
  for case_dir in "$ROOT"/cases/taint/$language/native-*; do
    fixture="$(basename "$case_dir")"
    args=("$case_dir" --overwrite)
    # Measured product defect, retained separately below: on this pin the
    # Python auto-detection emits `importCode.pythonsrc(...)`, which does not
    # compile against the product's own console. The documented explicit
    # `--language python` runs; the probe uses it so a crash cannot be
    # mistaken for a silence.
    [ "$language" = "python" ] && args+=(--language python)
    status=0
    (cd "$run_dir" && scan "${args[@]}") \
      > "$OUT/scan-$language-$fixture.txt" 2>&1 || status=$?
    summarize "$fixture" "$language" \
      "$(python3 -c 'import json,sys; print(json.dumps(sys.argv[1:]))' "${args[@]}")" \
      "$status"
  done
done

# Retain the auto-detection failure itself, once.
autodetect_status=0
(cd "$SCRATCH/run-python" && scan "$ROOT/cases/taint/python/native-source-sink-positive" --overwrite) \
  > "$SCRATCH/python-autodetect.txt" 2>&1 || autodetect_status=$?
{
  echo "exit status: $autodetect_status"
  grep -E 'E008|pythonsrc|error during script execution' "$SCRATCH/python-autodetect.txt" \
    | sed 's/\x1b\[[0-9;]*m//g' | head -8
} > "$OUT/python-autodetect-failure.txt"

# The binding check: on the Java source-sink positive's own CPG, the bundle's
# `call-to-exec` pattern matches zero methods while the call it is aimed at
# is present.
cat > "$SCRATCH/check.sc" <<'EOF'
@main def exec(cpgFile: String) = {
  importCpg(cpgFile)
  println("call-to-exec pattern `java.lang.Runtime.exec` matches methods: " +
    cpg.method("java.lang.Runtime.exec").size)
  println("method name `exec` matches methods: " + cpg.method("exec").size)
  println("calls to that method: " + cpg.method("exec").callIn.size)
  println("full name: " + cpg.method("exec").fullName.l)
}
EOF
cpg="$(ls "$SCRATCH"/run-java/workspace/native-source-sink-positive/cpg.bin* | head -1)"
# `importCpg` writes a workspace under the CWD too — keep it in the scratch.
(cd "$SCRATCH/run-java" && "$DIST/joern" --script "$SCRATCH/check.sc" --param cpgFile="$cpg" 2>/dev/null) \
  | grep -E 'matches methods|calls to|full name' \
  > "$OUT/call-to-exec-binding-check.txt"

echo "retained scan-bundle evidence under reports/raw/amendment-a26-joern-scan-native/"

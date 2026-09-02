#!/usr/bin/env bash
# Amendment A27's evidence: Semgrep CE's JavaScript and Java tool-native
# declines (A6/A7) are re-grounded on an ENUMERATION of the upstream tree at
# the pinned commit and a FIELD RUN of the pinned engine over every probe
# fixture.
#
# A6 and A7 retained all twelve JavaScript/Java cells unsupported from the
# vendored rule text alone, before Semgrep was invoked over a single native
# fixture — and it never was. A maintainer challenge to every 0-findings
# native row asks two questions this probe answers by measurement:
#
#   1. Was the vendored snapshot COMPLETE — did the vendoring copy only a
#      subset of the JavaScript/Java rules that existed at
#      semgrep/semgrep-rules@40b8c63f? The probe re-fetches the upstream
#      archive, verifies its SHA-256 against the recorded provenance digest,
#      and diffs the full `*.yaml` file list beneath each language's
#      `lang/security/` path against the vendored tree. It also greps the
#      ENTIRE upstream `javascript/`, `typescript/`, and `java/` trees for
#      the platform identities A8's Python promotion rule binds
#      (`os.environ`/`sys.argv` → the analogous `process.env`,
#      `process.argv`, `System.getenv`, `System.getProperty`), so "no analog
#      rule exists at that commit" is an enumerated fact rather than a
#      snapshot-scoped one.
#
#   2. Would a run have produced anything? The probe executes the pinned
#      Semgrep CE with the vendored snapshots over all twenty-four
#      JavaScript/Java native fixtures, with the exact argv the committed
#      runner uses, and retains per fixture the argv, the exit status, and
#      the finding and error counts alongside the full `--json` output.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome.
#
# Usage:
#   scripts/probe-semgrep-jsjava-native.sh [--semgrep <path>] [--archive <tar.gz>]
set -euo pipefail

SEMGREP="semgrep"
ARCHIVE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --semgrep) SEMGREP="$2"; shift 2 ;;
    --archive) ARCHIVE="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

COMMIT="40b8c63f75dc7c22c8a77482d73bfb864b146f7e"
# The archive digest the Python snapshot's provenance recorded at vendoring
# (adapters/semgrep/native/python/provenance.json → retrieval.archive_sha256):
# the probe re-fetches the same bytes or refuses to enumerate.
EXPECTED_ARCHIVE_SHA256="b7e483abf001c405a3e908251ff66cb198a26702aff5fe4c5f0c4b2fffec4919"
EXPECTED_VERSION="1.175.0"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a27-semgrep-jsjava-native"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
rm -rf "$OUT"
mkdir -p "$OUT"

VERSION="$("$SEMGREP" --version)"
if [ "$VERSION" != "$EXPECTED_VERSION" ]; then
  echo "refusing to probe: semgrep --version is '$VERSION', the pin is $EXPECTED_VERSION" >&2
  exit 1
fi

# ---------------------------------------------------------------------------
# 1. Fetch and verify the upstream archive at the pinned commit.
# ---------------------------------------------------------------------------
if [ -z "$ARCHIVE" ]; then
  ARCHIVE="$SCRATCH/semgrep-rules.tar.gz"
  curl -sSfL -o "$ARCHIVE" \
    "https://codeload.github.com/semgrep/semgrep-rules/tar.gz/$COMMIT"
fi
ACTUAL_SHA256="$(shasum -a 256 "$ARCHIVE" | cut -d' ' -f1)"
if [ "$ACTUAL_SHA256" != "$EXPECTED_ARCHIVE_SHA256" ]; then
  echo "refusing to enumerate: archive sha256 $ACTUAL_SHA256 != recorded $EXPECTED_ARCHIVE_SHA256" >&2
  exit 1
fi
tar -xzf "$ARCHIVE" -C "$SCRATCH"
UPSTREAM="$SCRATCH/semgrep-rules-$COMMIT"
{
  echo "upstream_repository: https://github.com/semgrep/semgrep-rules"
  echo "upstream_commit: $COMMIT"
  echo "archive_sha256: $ACTUAL_SHA256 (matches the digest recorded at vendoring)"
  echo "semgrep_version: $VERSION"
  echo "probed_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/upstream-archive-provenance.txt"

# ---------------------------------------------------------------------------
# 2. Snapshot completeness: vendored tree vs upstream <lang>/lang/security/.
# ---------------------------------------------------------------------------
enumerate() {
  local lang="$1"
  local upstream_dir="$UPSTREAM/$lang/lang/security"
  local vendored_dir="$ROOT/adapters/semgrep/native/$lang/rules"
  local report="$OUT/snapshot-enumeration-$lang.txt"
  (cd "$upstream_dir" && find . -name '*.yaml' | sed 's|^\./||' | sort) \
    > "$SCRATCH/$lang-upstream.list"
  (cd "$vendored_dir" && find . -name '*.yaml' | sed 's|^\./||' | sort) \
    > "$SCRATCH/$lang-vendored.list"
  {
    echo "language: $lang"
    echo "upstream_path: $lang/lang/security/ @ $COMMIT"
    echo "vendored_path: adapters/semgrep/native/$lang/rules/"
    echo "upstream_yaml_count: $(wc -l < "$SCRATCH/$lang-upstream.list" | tr -d ' ')"
    echo "vendored_yaml_count: $(wc -l < "$SCRATCH/$lang-vendored.list" | tr -d ' ')"
    echo
    echo "file-list diff (empty = the vendoring copied every rule document):"
    if diff "$SCRATCH/$lang-upstream.list" "$SCRATCH/$lang-vendored.list"; then
      echo "(none)"
    fi
    echo
    echo "byte comparison per rule document (LF-normalized, matching the"
    echo "repository's core.autocrlf=input storage of the snapshot):"
    local diffs=0
    while IFS= read -r rel; do
      if ! cmp -s <(tr -d '\r' < "$upstream_dir/$rel") "$vendored_dir/$rel"; then
        echo "  DIFFERS: $rel"
        diffs=$((diffs + 1))
      fi
    done < "$SCRATCH/$lang-upstream.list"
    if [ "$diffs" -eq 0 ]; then
      echo "  (every vendored document is byte-identical to upstream after CRLF->LF)"
    fi
  } > "$report"
}
enumerate javascript
enumerate java

# ---------------------------------------------------------------------------
# 3. Whole-tree platform-source enumeration: does ANY rule at the pinned
#    commit — inside or outside the vendored scope — bind the platform
#    identities the six templates probe, the way
#    python/lang/security/audit/dangerous-system-call-tainted-env-args.yaml
#    binds os.environ/sys.argv?
# ---------------------------------------------------------------------------
{
  echo "Whole-tree search of the upstream archive at $COMMIT for the platform"
  echo "identities that would make a JavaScript or Java analog of Python's"
  echo "audit/dangerous-system-call-tainted-env-args.yaml. Each block lists"
  echo "every matching rule document; an empty block means the identity"
  echo "occurs in no rule anywhere in the named trees."
  for probe in 'process.env' 'process.argv' 'child_process'; do
    echo
    echo "== javascript/ + typescript/ rules mentioning '$probe':"
    grep -rl --include='*.yaml' -F "$probe" \
      "$UPSTREAM/javascript" "$UPSTREAM/typescript" 2>/dev/null \
      | sed "s|$UPSTREAM/||" | sort || true
  done
  for probe in 'System.getenv' 'System.getProperty' 'System.setProperty'; do
    echo
    echo "== java/ rules mentioning '$probe':"
    grep -rl --include='*.yaml' -F "$probe" "$UPSTREAM/java" 2>/dev/null \
      | sed "s|$UPSTREAM/||" | sort || true
  done
} > "$OUT/platform-source-grep.txt"

# ---------------------------------------------------------------------------
# 4. Field run: the pinned engine, the vendored snapshot, every fixture —
#    the exact argv run_semgrep_native_case uses.
# ---------------------------------------------------------------------------
SUMMARY="$SCRATCH/summary-lines.txt"
: > "$SUMMARY"
scan() {
  local lang="$1" case_dir="$2"
  local case_name
  case_name="$(basename "$case_dir")"
  local rules="$ROOT/adapters/semgrep/native/$lang/rules"
  local json_out="$OUT/scan-$lang-$case_name.json"
  local txt_out="$OUT/scan-$lang-$case_name.txt"
  local status=0
  "$SEMGREP" scan --metrics=off --oss-only --disable-version-check \
    --no-git-ignore --quiet --json --config="$rules" "$case_dir" \
    > "$json_out" 2> "$SCRATCH/stderr.txt" || status=$?
  local results errors
  results="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["results"]))' "$json_out")"
  errors="$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["errors"]))' "$json_out")"
  {
    echo "argv: $SEMGREP scan --metrics=off --oss-only --disable-version-check --no-git-ignore --quiet --json --config=adapters/semgrep/native/$lang/rules $case_dir"
    echo "exit_status: $status"
    echo "findings: $results"
    echo "errors: $errors"
  } > "$txt_out"
  echo "$lang $case_name exit=$status findings=$results errors=$errors" >> "$SUMMARY"
}
for lang in javascript java; do
  for case_dir in "$ROOT/cases/taint/$lang"/native-*; do
    scan "$lang" "$case_dir"
  done
done

python3 - "$SUMMARY" "$OUT/scan-summary.json" "$VERSION" "$COMMIT" <<'PY'
import json, sys
lines = [l.split() for l in open(sys.argv[1]).read().splitlines()]
scans = [
    {
        "language": l[0],
        "case": l[1],
        "exit_status": int(l[2].split("=")[1]),
        "findings": int(l[3].split("=")[1]),
        "errors": int(l[4].split("=")[1]),
    }
    for l in lines
]
json.dump(
    {
        "schema_version": 1,
        "evidence_kind": "retained-field-evaluation",
        "tool": "semgrep",
        "witnessed_tool_version": sys.argv[3],
        "upstream_commit": sys.argv[4],
        "scan_count": len(scans),
        "total_findings": sum(s["findings"] for s in scans),
        "total_errors": sum(s["errors"] for s in scans),
        "scans": scans,
    },
    open(sys.argv[2], "w"),
    indent=2,
    sort_keys=True,
)
print(file=open(sys.argv[2], "a"))
PY

echo "retained under $OUT"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["scan_count"], "scans,", d["total_findings"], "findings,", d["total_errors"], "errors")' "$OUT/scan-summary.json"

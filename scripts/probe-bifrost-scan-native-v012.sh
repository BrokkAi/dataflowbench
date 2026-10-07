#!/usr/bin/env bash
# Amendment A33: a bounded native-surface evaluation of the public Bifrost
# v0.12.0 binary. This is versioned separately from the hash-bound historical
# A32 probe so its evidence cannot overwrite or be confused with that result.
#
# The probe retains the same shipped-catalog, thirty-six-fixture, activation
# narrowing, and positive-control scope as A32. Every outcome and completion
# field is derived from the v0.12.0 JSON result; no prior result is assumed.
#
# Failed runs retain their scratch root for diagnosis. A successful run stages
# its evidence and refuses to replace an existing A33 output directory.
#
# Usage:
#   scripts/probe-bifrost-scan-native-v012.sh [--bifrost <path>]

set -euo pipefail

BIFROST="bifrost"
while [ $# -gt 0 ]; do
  case "$1" in
    --bifrost) BIFROST="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a33-bifrost-v012-scan-native"
if [ -e "$OUT" ] || [ -L "$OUT" ]; then
  echo "refusing to overwrite existing probe output: $OUT" >&2
  exit 1
fi
SCRATCH="$(mktemp -d)"
trap 'probe_status=$?; if [ "$probe_status" -eq 0 ]; then rm -rf "$SCRATCH"; else echo "retained failed probe scratch: $SCRATCH" >&2; fi' EXIT
STAGED_OUT="$SCRATCH/amendment-a33-bifrost-v012-scan-native"
mkdir -p "$STAGED_OUT" "$STAGED_OUT/scan" "$STAGED_OUT/positive-control"
OUT="$STAGED_OUT"

BIN="$(command -v "$BIFROST")"
EXPECTED_BUILD_ID="676def6c6615002002b1bb9d25211ad1476a5b5d"
EXPECTED_SHA256="168cf91d61f7504fbabf77974bfe53cdcc6f41abfbb727b7b152db18a3c4b545"
EVALUATION_DATE="2026-09-04"
ACTUAL_BUILD_ID="$("$BIFROST" --build-identity)"
ACTUAL_SHA256="$(shasum -a 256 "$BIN" | cut -d' ' -f1)"
test "$ACTUAL_BUILD_ID" = "$EXPECTED_BUILD_ID" || {
  echo "wrong Bifrost build identity: expected $EXPECTED_BUILD_ID, got $ACTUAL_BUILD_ID" >&2
  exit 1
}
test "$ACTUAL_SHA256" = "$EXPECTED_SHA256" || {
  echo "wrong Bifrost binary digest: expected $EXPECTED_SHA256, got $ACTUAL_SHA256" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# 1. The pin, witnessed. The banner is the same four lines Amendment A31 began
#    retaining beside every Bifrost population; the build identity is the one a
#    release-scope freeze requires (a crates.io build answers `unknown`).
# ---------------------------------------------------------------------------
{
  echo "binary: $BIN"
  echo "binary sha256: $ACTUAL_SHA256"
  echo "--build-identity: $ACTUAL_BUILD_ID"
  echo "--version:"
  "$BIFROST" --version | sed 's/^/  /'
} > "$OUT/witnessed-pin.txt"

# ---------------------------------------------------------------------------
# 2. The shipped entry point exists, and what it says it activates.
# ---------------------------------------------------------------------------
"$BIFROST" --help          > "$OUT/help-top-level.txt" 2>&1
"$BIFROST" scan --help     > "$OUT/help-scan.txt"      2>&1

# ---------------------------------------------------------------------------
# 3. The shipped catalog, enumerated from the binary. `scan
#    --list-builtin-policies` is the scan surface's own discovery flag; the
#    flag surface's `--list-policies` is the one the preregistration read. The
#    probe retains both and proves they are the same document, so no claim
#    below turns on which flag was used.
# ---------------------------------------------------------------------------
"$BIFROST" scan --list-builtin-policies > "$OUT/builtin-policy-catalog.json"
"$BIFROST" --list-policies              > "$SCRATCH/list-policies.json"
if diff -q "$OUT/builtin-policy-catalog.json" "$SCRATCH/list-policies.json" > /dev/null; then
  echo "identical: \`bifrost scan --list-builtin-policies\` and \`bifrost --list-policies\` print the same catalog document" \
    > "$OUT/catalog-flag-equivalence.txt"
else
  echo "DIFFERENT — the two discovery flags disagree; every catalog claim below must name which flag it read" \
    > "$OUT/catalog-flag-equivalence.txt"
  diff "$OUT/builtin-policy-catalog.json" "$SCRATCH/list-policies.json" \
    >> "$OUT/catalog-flag-equivalence.txt" || true
  echo "catalog discovery flags disagree" >&2
  exit 1
fi

python3 - "$OUT" <<'PY'
import json, sys
out = sys.argv[1]
catalog = json.load(open(f"{out}/builtin-policy-catalog.json"))
lines = []
for pack in catalog["packs"]:
    lines.append(f"pack {pack['id']}@{pack['version']} policies={len(pack['policies'])} — {pack['name']}")
    lines.append(f"  {pack['description']}")
    for policy in pack["policies"]:
        lines.append(
            f"  - {policy['id']}  category={policy['category']}"
            f"  languages={','.join(policy['supported_languages'])}"
        )
        lines.append(f"      path={policy['path']}")
        lines.append(f"      required_capabilities={','.join(policy['required_capabilities'])}")
open(f"{out}/catalog-index.txt", "w").write("\n".join(lines) + "\n")
PY

# ---------------------------------------------------------------------------
# 4. What the servlet-to-JDBC security policy declares — read from
#    the v0.12.0 executable's own embedded copy rather than from documentation.
#    The catalog retained above is authoritative for the complete pack selected
#    by this binary;
#    this source records the policy exposed by this versioned binary.
# ---------------------------------------------------------------------------
strings -n 6 "$BIN" > "$SCRATCH/bin-strings.txt"
python3 - "$SCRATCH/bin-strings.txt" "$OUT/security-policy-source.rqlp" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
start = text.index('policies/jvm/servlet-parameter-to-jdbc.rqlp')
start = text.index('(policy', start)
# The embedded blob ends at the closing paren of the top-level `(policy …)`.
depth, end = 0, None
for index, character in enumerate(text[start:], start):
    if character == '(':
        depth += 1
    elif character == ')':
        depth -= 1
        if depth == 0:
            end = index + 1
            break
assert end is not None, "unterminated embedded policy document"
open(sys.argv[2], "w").write(text[start:end] + "\n")
PY
{
  echo "extracted from: $BIN"
  echo "embedded path:  policies/jvm/servlet-parameter-to-jdbc.rqlp"
  echo "sha256 of the extracted text: $(shasum -a 256 "$OUT/security-policy-source.rqlp" | cut -d' ' -f1)"
  echo "catalog authored_hash and resolved_semantic_hash for the same policy:"
  python3 -c "
import json
for pack in json.load(open('$OUT/builtin-policy-catalog.json'))['packs']:
    for policy in pack['policies']:
        if policy['id'] == 'bifrost.security.java.servlet-parameter-to-jdbc':
            print('  authored_hash: ' + policy['authored_hash'])
            print('  resolved_semantic_hash: ' + policy['resolved_semantic_hash'])
"
} > "$OUT/security-policy-provenance.txt"

# ---------------------------------------------------------------------------
# 5. `bifrost scan` over all thirty-six committed tool-native fixtures. The
#    product as shipped: no --policy-file, no selector, no benchmark input of
#    any kind. Every fixture directory is copied to a scratch root so the scan
#    cannot see the repository around it, and each fixture's `case.json` is
#    left out: it is benchmark metadata, not source under analysis.
# ---------------------------------------------------------------------------
for language in java javascript python; do
  for case_dir in "$ROOT"/cases/taint/$language/native-*; do
    fixture="$(basename "$case_dir")"
    work="$SCRATCH/work/$language/$fixture"
    mkdir -p "$work"
    find "$case_dir" -type f ! -name case.json -exec cp {} "$work/" \;

    status=0
    "$BIFROST" scan "$work" --format json --evaluation-date "$EVALUATION_DATE" \
      > "$SCRATCH/scan.json" 2> "$OUT/scan/$language-$fixture.stderr" || status=$?

    cp "$SCRATCH/scan.json" "$OUT/scan/$language-$fixture.full.json"
    python3 - "$SCRATCH/scan.json" "$language" "$fixture" "$status" "$OUT" <<'PY'
import json, sys
report_path, language, fixture, status, out = sys.argv[1:6]
report = json.load(open(report_path))
catalog = json.load(open(f"{out}/builtin-policy-catalog.json"))
expected_ids = {
    policy["id"]
    for pack in catalog["packs"]
    for policy in pack["policies"]
}
actual_ids = {run["policy_id"] for run in report["runs"]}
assert len(report["runs"]) == len(expected_ids), \
    f"{language}/{fixture}: expected {len(expected_ids)} policy runs"
assert actual_ids == expected_ids, \
    f"{language}/{fixture}: scan/catalog policy mismatch"
completion_types = {run["completion"]["type"] for run in report["runs"]}
assert completion_types <= {"complete", "inconclusive"}, \
    f"{language}/{fixture}: unexpected completion types {sorted(completion_types)}"
total_findings = sum(len(run["findings"]) for run in report["runs"])
expected_status = (
    2 if completion_types != {"complete"}
    else 1 if total_findings
    else 0
)
assert int(status) == expected_status, \
    f"{language}/{fixture}: exit {status} does not match result state"
outcome = (
    "inconclusive"
    if completion_types != {"complete"}
    else "finding" if total_findings else "no-finding"
)
security = next(
    run for run in report["runs"]
    if run["policy_id"] == "bifrost.security.java.servlet-parameter-to-jdbc"
)
security_runs = [
    run for run in report["runs"]
    if run["policy_id"].startswith("bifrost.security.")
]
metrics = {metric["name"]: metric["value"] for metric in security["work"]["metrics"]}
summary = {
    "probe": fixture,
    "language": language,
    "invocation": ["bifrost", "scan", "<fixture>", "--format", "json",
                   "--evaluation-date", "2026-09-04"],
    "scan_exit_status": int(status),
    "activated_packs": [
        {"id": pack["id"], "version": pack["version"], "policies": len(pack["policies"])}
        for pack in catalog["packs"]
    ],
    "policies_evaluated": len(report["runs"]),
    "policy_completions": sorted({
        f"{run['policy_id']}={run['completion']['type']}" for run in report["runs"]
    }),
    "outcome": outcome,
    "outcome_basis": {
        "completion_types": sorted(completion_types),
        "total_findings": total_findings,
    },
    "total_findings": total_findings,
    "findings_by_policy": {
        run["policy_id"]: len(run["findings"])
        for run in report["runs"] if run["findings"]
    },
    "security_policy": {
        "policy_id": security["policy_id"],
        "analysis_type": security["analysis_type"],
        "completion": security["completion"],
        "outcome": (
            "inconclusive"
            if security["completion"]["type"] != "complete"
            else "finding" if security["findings"] else "no-finding"
        ),
        "findings": len(security["findings"]),
        "compiled_source_endpoints": metrics.get("taint.compiled_source_endpoints"),
        "compiled_sink_endpoints": metrics.get("taint.compiled_sink_endpoints"),
        "selector_scans": metrics.get("taint.selector_scans"),
        "diagnostics": [
            {"severity": d["severity"], "family": d["family"], "message": d["message"]}
            for d in security["diagnostics"]
        ],
    },
    "security_policies": [
        {
            "policy_id": run["policy_id"],
            "analysis_type": run["analysis_type"],
            "completion": run["completion"],
            "findings": len(run["findings"]),
            "metrics": {
                metric["name"]: metric["value"]
                for metric in run["work"]["metrics"]
                if metric["name"].startswith("taint.")
            },
        }
        for run in security_runs
    ],
    "evidence_kind": "retained-shipped-scan-probe",
}
with open(f"{out}/scan/{language}-{fixture}.json", "w") as handle:
    json.dump(summary, handle, indent=2)
    handle.write("\n")
print(f"{language}/{fixture}: exit={status} findings={summary['total_findings']} "
      f"src_endpoints={summary['security_policy']['compiled_source_endpoints']} "
      f"sink_endpoints={summary['security_policy']['compiled_sink_endpoints']}")
PY
  done
done

# ---------------------------------------------------------------------------
# 6. The retained activation, run beside the shipped default on one fixture, so
#    the narrowing is measured rather than argued: `--policy-pack
#    bifrost.code-smells` is an explicit selection that REPLACES the built-in
#    default, and the security pack never loads under it.
# ---------------------------------------------------------------------------
probe_fixture="$SCRATCH/work/java/native-source-sink-positive"
retained_status=0
"$BIFROST" --root "$probe_fixture" --policy-pack bifrost.code-smells \
  --format json --evaluation-date "$EVALUATION_DATE" \
  > "$SCRATCH/retained-activation.json" 2> "$OUT/retained-activation.stderr" || retained_status=$?
default_status=0
"$BIFROST" --root "$probe_fixture" --policy \
  --format json --evaluation-date "$EVALUATION_DATE" \
  > "$SCRATCH/default-activation.json" 2> "$OUT/default-activation.stderr" || default_status=$?
python3 - "$SCRATCH/retained-activation.json" "$SCRATCH/default-activation.json" "$retained_status" "$default_status" "$OUT" <<'PY'
import json, sys
retained, default, retained_status, default_status, out = sys.argv[1:6]
def report_state(path):
    report = json.load(open(path))
    ids = sorted(run["policy_id"] for run in report["runs"])
    completions = {run["completion"]["type"] for run in report["runs"]}
    assert completions <= {"complete", "inconclusive"}, \
        f"unexpected completion types {sorted(completions)} in {path}"
    return ids, completions
retained_ids, retained_completions = report_state(retained)
default_ids, default_completions = report_state(default)
def expected_status(report_path, completions):
    report = json.load(open(report_path))
    findings = sum(len(run["findings"]) for run in report["runs"])
    return 2 if completions != {"complete"} else 1 if findings else 0
expected_retained_status = expected_status(retained, retained_completions)
expected_default_status = expected_status(default, default_completions)
assert int(retained_status) == expected_retained_status, \
    f"retained activation exit {retained_status} does not match {sorted(retained_completions)}"
assert int(default_status) == expected_default_status, \
    f"default activation exit {default_status} does not match {sorted(default_completions)}"
catalog = json.load(open(f"{out}/builtin-policy-catalog.json"))
catalog_ids = {
    pack["id"]: {policy["id"] for policy in pack["policies"]}
    for pack in catalog["packs"]
}
expected_retained = catalog_ids["bifrost.code-smells"]
expected_security = catalog_ids["bifrost.security"]
assert set(retained_ids) == expected_retained, \
    f"code-smell activation differs from catalog: {sorted(set(retained_ids) ^ expected_retained)}"
assert set(default_ids) == expected_retained | expected_security, \
    f"default activation differs from catalog: {sorted(set(default_ids) ^ (expected_retained | expected_security))}"
assert set(default_ids) - set(retained_ids) == expected_security
summary = {
    "fixture": "cases/taint/java/native-source-sink-positive",
    "retained_activation": {
        "arguments": ["--policy-pack", "bifrost.code-smells"],
        "policies_evaluated": len(retained_ids),
        "completion_types": sorted(retained_completions),
        "security_pack_loaded": any(p.startswith("bifrost.security.") for p in retained_ids),
    },
    "shipped_default_activation": {
        "arguments": ["--policy"],
        "policies_evaluated": len(default_ids),
        "completion_types": sorted(default_completions),
        "security_pack_loaded": any(p.startswith("bifrost.security.") for p in default_ids),
    },
    "policies_the_retained_activation_excludes": sorted(set(default_ids) - set(retained_ids)),
    "evidence_kind": "retained-activation-narrowing-check",
}
with open(f"{out}/activation-narrowing.json", "w") as handle:
    json.dump(summary, handle, indent=2)
    handle.write("\n")
print("activation narrowing:", json.dumps(summary["policies_the_retained_activation_excludes"]))
PY

# 7. Positive-control attempt. Its outcome, completion, findings, and
#    diagnostics are recorded from the actual v0.12.0 report.
# ---------------------------------------------------------------------------
control_root="$SCRATCH/positive-control"
mkdir -p "$control_root/src/main/java/dfb"
cat > "$control_root/pom.xml" <<'POM'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>dfb</groupId>
  <artifactId>bifrost-security-control</artifactId>
  <version>1.0.0</version>
  <packaging>jar</packaging>
  <properties>
    <maven.compiler.release>17</maven.compiler.release>
  </properties>
  <dependencies>
    <dependency>
      <groupId>jakarta.servlet</groupId>
      <artifactId>jakarta.servlet-api</artifactId>
      <version>6.1.0</version>
      <scope>provided</scope>
    </dependency>
  </dependencies>
</project>
POM
cat > "$control_root/src/main/java/dfb/Control.java" <<'JAVA'
package dfb;

import jakarta.servlet.http.HttpServletRequest;
import java.sql.Connection;
import java.sql.SQLException;
import java.sql.Statement;

/** The exact flow `bifrost.security.java.servlet-parameter-to-jdbc` names. */
public final class Control {
    public void handle(HttpServletRequest request, Connection connection) throws SQLException {
        String name = request.getParameter("name");
        String sql = "SELECT * FROM users WHERE name = '" + name + "'";
        Statement statement = connection.createStatement();
        statement.execute(sql);
    }
}
JAVA
cp "$control_root/pom.xml" "$OUT/positive-control/pom.xml"
cp "$control_root/src/main/java/dfb/Control.java" "$OUT/positive-control/Control.java"

control_status=0
"$BIFROST" scan "$control_root" --format json --evaluation-date "$EVALUATION_DATE" \
  > "$SCRATCH/control.json" 2> "$OUT/positive-control/scan.stderr" || control_status=$?
python3 - "$SCRATCH/control.json" "$control_status" "$OUT" <<'PY'
import json, sys
report_path, status, out = sys.argv[1:4]
report = json.load(open(report_path))
security = next(
    run for run in report["runs"]
    if run["policy_id"] == "bifrost.security.java.servlet-parameter-to-jdbc"
)
metrics = {metric["name"]: metric["value"] for metric in security["work"]["metrics"]}
completion_types = {run["completion"]["type"] for run in report["runs"]}
total_findings = sum(len(run["findings"]) for run in report["runs"])
expected_status = (
    2 if completion_types != {"complete"}
    else 1 if total_findings
    else 0
)
assert int(status) == expected_status, "control exit status does not match report state"
completion_type = security["completion"]["type"]
finding_count = len(security["findings"])
outcome = (
    "inconclusive"
    if completion_type != "complete"
    else "finding" if finding_count else "no-finding"
)
summary = {
    "shape": "jakarta.servlet HttpServletRequest.getParameter -> java.sql.Statement.execute",
    "scan_exit_status": int(status),
    "dependency_pack_decisions": report["packs"]["decisions"],
    "completion": security["completion"],
    "outcome": outcome,
    "outcome_basis": {
        "completion_type": completion_type,
        "finding_count": finding_count,
    },
    "findings": finding_count,
    "compiled_source_endpoints": metrics.get("taint.compiled_source_endpoints"),
    "compiled_sink_endpoints": metrics.get("taint.compiled_sink_endpoints"),
    "diagnostics": [
        {"severity": d["severity"], "family": d["family"], "message": d["message"]}
        for d in security["diagnostics"]
    ],
    "evidence_kind": "retained-positive-control-attempt",
}
with open(f"{out}/positive-control/result.json", "w") as handle:
    json.dump(summary, handle, indent=2)
    handle.write("\n")
readme = (
    "This positive-control attempt records the v0.12.0 result produced by the scan.\n"
    "The outcome is derived from the security-policy completion and finding count\n"
    "in result.json; no prior result is assumed.\n\n"
    f"Observed outcome: {summary['outcome']}\n"
    f"Observed completion: {json.dumps(summary['completion'], sort_keys=True)}\n"
    f"Observed findings: {summary['findings']}\n\n"
    "The source uses the exact servlet-parameter-to-JDBC shape named by the policy\n"
    "in a Maven project declaring jakarta.servlet-api:6.1.0. Diagnostics and\n"
    "dependency-pack decisions are retained in result.json and the full stderr is\n"
    "beside this file.\n"
)
open(f"{out}/positive-control/README.txt", "w").write(readme)
print("positive control:", summary["outcome"], summary["completion"])
PY

echo
echo "retained scan-surface evidence under reports/raw/amendment-a33-bifrost-v012-scan-native/"

# Publish only after every assertion above has passed. A failed rerun leaves
# its scratch root intact, and an existing A33 output is never replaced.
FINAL_OUT="$ROOT/reports/raw/amendment-a33-bifrost-v012-scan-native"
if [ -e "$FINAL_OUT" ] || [ -L "$FINAL_OUT" ]; then
  echo "refusing to overwrite existing probe output: $FINAL_OUT" >&2
  exit 1
fi
mv -n "$STAGED_OUT" "$FINAL_OUT"
if [ -e "$STAGED_OUT" ]; then
  echo "probe output appeared during publication; retained failed scratch: $SCRATCH" >&2
  exit 1
fi

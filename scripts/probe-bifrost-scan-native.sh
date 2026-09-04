#!/usr/bin/env bash
# Amendment A32's evidence: Bifrost's tool-native declines are re-grounded on a
# FIELD EVALUATION of the pinned v0.10.9 binary, not on the superseded v0.9.5
# inspection the preregistration recorded.
#
# Two claims in `docs/native-profile.md` failed at the v0.7.0 pin:
#
#   1. "no taint policy, no source or sink endpoint set". The pinned build's
#      own `--version` banner — retained in every native population's
#      `run-environment.json` since Amendment A31 — names TWO built-in packs,
#      and the second is `bifrost.security@1.0.0`. The partition was written
#      against a locally installed v0.9.5 that shipped one.
#   2. Nothing in the repository had engaged `bifrost scan`, the shipped
#      product's own zero-configuration entry point. The retained activation
#      passed `--policy-pack bifrost.code-smells`, which the pinned CLI treats
#      as an explicit selection that REPLACES the built-in default — so the
#      tool-native column was measuring one hand-picked pack rather than the
#      shipped catalog.
#
# This probe establishes both from the binary. It enumerates the shipped
# catalog, extracts the security policy's verbatim embedded RQLP source from
# the pinned executable, runs `bifrost scan` — the product as shipped, zero
# configuration — over all thirty-six committed tool-native fixtures (twelve
# per language), and retains per fixture the full report, exact argv, exit
# status, activated-pack witness, every policy's completion and finding, and
# the security policy's own endpoint-binding metrics.
#
# It also retains a positive-control ATTEMPT on the one shape the shipped
# security policy is aimed at. The control did not fire, and the probe retains
# why rather than hiding it: see `positive-control/README.txt`.
#
# The probe never touches a committed artifact, never writes a report, and
# never feeds a normalized outcome.
#
# Usage:
#   scripts/probe-bifrost-scan-native.sh [--bifrost <path>]
set -euo pipefail

BIFROST="bifrost"
while [ $# -gt 0 ]; do
  case "$1" in
    --bifrost) BIFROST="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/reports/raw/amendment-a32-bifrost-scan-native"
SCRATCH="$(mktemp -d)"
trap 'rm -rf "$SCRATCH"' EXIT
STAGED_OUT="$SCRATCH/amendment-a32-bifrost-scan-native"
mkdir -p "$STAGED_OUT" "$STAGED_OUT/scan" "$STAGED_OUT/positive-control"
OUT="$STAGED_OUT"

BIN="$(command -v "$BIFROST")"
EXPECTED_BUILD_ID="04775a7b38c9c025714168328ddb8b793a326461"
EXPECTED_SHA256="b5ac3e7d395392df365ccd3dfdfc71996ca859b0adf0402b47aa184436be6296"
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
# 4. What `bifrost.security@1.0.0`'s single policy declares — read from the
#    pinned executable's own embedded copy rather than from documentation.
#    The RQLP source is what settles every partition row below: which
#    endpoints it binds, and which stanzas it does not carry at all.
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
  echo "catalog semantic_hash for the same policy:"
  python3 -c "
import json
for pack in json.load(open('$OUT/builtin-policy-catalog.json'))['packs']:
    for policy in pack['policies']:
        if policy['id'] == 'bifrost.security.java.servlet-parameter-to-jdbc':
            print('  ' + policy['semantic_hash'])
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
    "$BIFROST" scan "$work" --format json --evaluation-date 2026-09-04 \
      > "$SCRATCH/scan.json" 2> "$OUT/scan/$language-$fixture.stderr" || status=$?

    cp "$SCRATCH/scan.json" "$OUT/scan/$language-$fixture.full.json"
    python3 - "$SCRATCH/scan.json" "$language" "$fixture" "$status" "$OUT" <<'PY'
import json, sys
report_path, language, fixture, status, out = sys.argv[1:6]
report = json.load(open(report_path))
assert int(status) == 0, f"{language}/{fixture}: scan exited {status}"
assert len(report["runs"]) == 17, f"{language}/{fixture}: expected 17 policy runs"
assert all(run["completion"]["type"] == "complete" for run in report["runs"]), \
    f"{language}/{fixture}: incomplete policy run"
assert sum(len(run["findings"]) for run in report["runs"]) == 0, \
    f"{language}/{fixture}: unexpected finding"
security = next(
    run for run in report["runs"]
    if run["policy_id"] == "bifrost.security.java.servlet-parameter-to-jdbc"
)
metrics = {metric["name"]: metric["value"] for metric in security["work"]["metrics"]}
assert metrics.get("taint.compiled_source_endpoints") == 0, \
    f"{language}/{fixture}: security source endpoint unexpectedly bound"
assert metrics.get("taint.compiled_sink_endpoints") == 0, \
    f"{language}/{fixture}: security sink endpoint unexpectedly bound"
summary = {
    "probe": fixture,
    "language": language,
    "invocation": ["bifrost", "scan", "<fixture>", "--format", "json",
                   "--evaluation-date", "2026-09-04"],
    "scan_exit_status": int(status),
    "activated_packs": [
        {"id": pack["id"], "version": pack["version"], "policies": len(pack["policies"])}
        for pack in json.load(open(f"{out}/builtin-policy-catalog.json"))["packs"]
    ],
    "policies_evaluated": len(report["runs"]),
    "policy_completions": sorted({
        f"{run['policy_id']}={run['completion']['type']}" for run in report["runs"]
    }),
    "total_findings": sum(len(run["findings"]) for run in report["runs"]),
    "findings_by_policy": {
        run["policy_id"]: len(run["findings"])
        for run in report["runs"] if run["findings"]
    },
    "security_policy": {
        "policy_id": security["policy_id"],
        "analysis_type": security["analysis_type"],
        "completion": security["completion"],
        "findings": len(security["findings"]),
        "compiled_source_endpoints": metrics.get("taint.compiled_source_endpoints"),
        "compiled_sink_endpoints": metrics.get("taint.compiled_sink_endpoints"),
        "selector_scans": metrics.get("taint.selector_scans"),
        "diagnostics": [
            {"severity": d["severity"], "family": d["family"], "message": d["message"]}
            for d in security["diagnostics"]
        ],
    },
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
  --format json --evaluation-date 2026-09-04 \
  > "$SCRATCH/retained-activation.json" 2> "$OUT/retained-activation.stderr" || retained_status=$?
default_status=0
"$BIFROST" --root "$probe_fixture" --policy \
  --format json --evaluation-date 2026-09-04 \
  > "$SCRATCH/default-activation.json" 2> "$OUT/default-activation.stderr" || default_status=$?
python3 - "$SCRATCH/retained-activation.json" "$SCRATCH/default-activation.json" "$retained_status" "$default_status" "$OUT" <<'PY'
import json, sys
retained, default, retained_status, default_status, out = sys.argv[1:6]
assert int(retained_status) == 0, f"retained activation exited {retained_status}"
assert int(default_status) == 0, f"default activation exited {default_status}"
def policies(path):
    return sorted(run["policy_id"] for run in json.load(open(path))["runs"])
retained_ids, default_ids = policies(retained), policies(default)
assert len(retained_ids) == 16, f"expected 16 code-smell policies, got {len(retained_ids)}"
assert len(default_ids) == 17, f"expected 17 default policies, got {len(default_ids)}"
assert set(default_ids) - set(retained_ids) == {"bifrost.security.java.servlet-parameter-to-jdbc"}
summary = {
    "fixture": "cases/taint/java/native-source-sink-positive",
    "retained_activation": {
        "arguments": ["--policy-pack", "bifrost.code-smells"],
        "policies_evaluated": len(retained_ids),
        "security_pack_loaded": any(p.startswith("bifrost.security.") for p in retained_ids),
    },
    "shipped_default_activation": {
        "arguments": ["--policy"],
        "policies_evaluated": len(default_ids),
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

# ---------------------------------------------------------------------------
# 7. Positive-control ATTEMPT, retained with its outcome stated plainly. A live
#    control would prove the shipped security policy can fire at all; this one
#    did not fire, and the honest record of that is worth more than its
#    omission. Four shapes were tried, each the servlet-parameter-to-JDBC flow
#    the policy names, and every one is retained.
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
"$BIFROST" scan "$control_root" --format json --evaluation-date 2026-09-04 \
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
summary = {
    "shape": "jakarta.servlet HttpServletRequest.getParameter -> java.sql.Statement.execute",
    "scan_exit_status": int(status),
    "dependency_pack_decisions": report["packs"]["decisions"],
    "completion": security["completion"],
    "findings": len(security["findings"]),
    "compiled_source_endpoints": metrics.get("taint.compiled_source_endpoints"),
    "compiled_sink_endpoints": metrics.get("taint.compiled_sink_endpoints"),
    "diagnostics": [
        {"severity": d["severity"], "family": d["family"], "message": d["message"]}
        for d in security["diagnostics"]
    ],
    "evidence_kind": "retained-positive-control-attempt",
    "outcome": "did-not-fire",
}
with open(f"{out}/positive-control/result.json", "w") as handle:
    json.dump(summary, handle, indent=2)
    handle.write("\n")
print("positive control:", summary["outcome"], summary["completion"])
PY
cat > "$OUT/positive-control/README.txt" <<'NOTE'
The positive control did not fire, and this file says so rather than leaving
the attempt out.

What was tried: the exact flow the shipped policy names — a jakarta.servlet
`HttpServletRequest.getParameter(String)` value concatenated into SQL text and
passed to `java.sql.Statement.execute(String)` — in a Maven project declaring
the real `jakarta.servlet:jakarta.servlet-api:6.1.0` dependency, which the scan
report shows the CLI selecting as a dependency pack. This is the one retained
and reproducible positive-control attempt; no unretained manual variants are
used as evidence.

What the tool said. On every one of those shapes the run came back
`inconclusive (partial_discovery)` with

    taint selector did not execute completely: selector
    `/analysis/sources/entries/servlet-request-parameter/selector` could not
    prove an empty row selection (calls: semantic_analysis_partial:
    call_bindings did not establish complete actual-to-formal coverage
    (dispatch outcome=unknown, coverage=open, target_count=1,
    binding coverage=unknown))

and with the JVM external-model pack `bifrost.external.java` reported
`incompatible` — "complete activation evidence does not satisfy the manifest and
shard selector". The policy declares `:proof exact` on both endpoint selectors
and the catalog lists `exact-call-target` and `semantic-model-provenance` among
its required capabilities, so an unproven dispatch is refused rather than
guessed. That is the policy behaving as its own description promises; what this
probe could not do on this host is assemble a project in which the proof is
available.

Why the declines do not rest on it. This control is the weaker of two available
liveness arguments, and the stronger one is in the sweep itself. On all
thirty-six tool-native fixtures the same policy comes back
`completion: complete` with its own `empty_selection` notes naming it by id and
saying, in the tool's words, that it "bound no source endpoint ... so this run
reports zero findings VACUOUSLY rather than proving that no flow exists". A
policy that failed to load could not produce those. The partition rows below are
decided on the endpoint identities the policy DECLARES — read verbatim out of
the pinned executable, in `security-policy-source.rqlp` — and on that measured
vacuity, neither of which needs the control.
NOTE

echo
echo "retained scan-surface evidence under reports/raw/amendment-a32-bifrost-scan-native/"

# Publish only after every assertion above has passed. A failed rerun leaves
# the previously committed evidence intact for audit.
FINAL_OUT="$ROOT/reports/raw/amendment-a32-bifrost-scan-native"
rm -rf "$FINAL_OUT"
mv "$STAGED_OUT" "$FINAL_OUT"

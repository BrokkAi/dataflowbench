#!/usr/bin/env bash
set -euo pipefail

audit_dir="${1:-$(cd "$(dirname "$0")" && pwd)}"
manifest="$audit_dir/next-pin-manifest.json"
summary="$audit_dir/SUMMARY.json"
requests="$audit_dir/requests.jsonl"

fail() { printf 'FAIL: %s\n' "$1" >&2; exit 1; }

jq empty "$manifest" || fail 'manifest JSON does not parse'
jq empty "$summary" || fail 'summary JSON does not parse'

expected_count="$(jq -r '.audit.request_count' "$manifest")"
actual_count="$(wc -l < "$requests" | tr -d ' ')"
[ "$actual_count" = "$expected_count" ] || fail "request count $actual_count != manifest $expected_count"

expected_statuses="$(jq -c '.audit.http_status_counts | to_entries | sort_by(.key)' "$manifest")"
actual_statuses="$(jq -s -c 'group_by(.http_status) | map({key:.[0].http_status,value:length}) | sort_by(.key)' "$requests")"
[ "$actual_statuses" = "$expected_statuses" ] || fail "status counts $actual_statuses != manifest $expected_statuses"

while IFS= read -r record; do
  name="$(printf '%s\n' "$record" | jq -r '.name')"
  body_rel="$(printf '%s\n' "$record" | jq -r '.body_path')"
  headers_rel="$(printf '%s\n' "$record" | jq -r '.headers_path')"
  body_sha="$(printf '%s\n' "$record" | jq -r '.body_sha256')"
  headers_sha="$(printf '%s\n' "$record" | jq -r '.headers_sha256')"
  body="$audit_dir/$body_rel"
  headers="$audit_dir/$headers_rel"
  [ -f "$body" ] || fail "$name body missing: $body_rel"
  [ -f "$headers" ] || fail "$name headers missing: $headers_rel"
  actual_body_sha="$(shasum -a 256 "$body" | awk '{print $1}')"
  actual_headers_sha="$(shasum -a 256 "$headers" | awk '{print $1}')"
  [ "$actual_body_sha" = "$body_sha" ] || fail "$name body digest mismatch"
  [ "$actual_headers_sha" = "$headers_sha" ] || fail "$name headers digest mismatch"
  jq empty "$body" || fail "$name body is not JSON"
done < "$requests"

if find "$audit_dir/raw" -name '*.stderr' -type f -size +0c -print -quit | grep -q .; then
  fail 'one or more captured requests wrote stderr'
fi

jq -e '.audit.worktree_status == "dirty_shared_preexisting" and .audit.worktree_dirty == true' "$manifest" >/dev/null || fail 'shared dirty worktree status missing'
jq -e '.targets[] | select(.name == "bifrost" and .candidate_pin == "v0.11.5")' "$manifest" >/dev/null || fail 'Bifrost candidate assertion failed'
jq -e '.targets[] | select(.name == "codeql-cli" and .candidate_pin == "v2.27.1")' "$manifest" >/dev/null || fail 'CodeQL CLI candidate assertion failed'
jq -e '.targets[] | select(.name == "joern" and .candidate_pin == "v4.0.633")' "$manifest" >/dev/null || fail 'Joern candidate assertion failed'
jq -e '.targets[] | select(.name == "semgrep" and .candidate_pin == "v1.177.0" and .decision == "hold-current")' "$manifest" >/dev/null || fail 'Semgrep hold assertion failed'
jq -e '.targets[] | select(.name == "semgrep-rules" and .exact_compare.ahead_by == 3 and .exact_compare.behind_by == 0 and .candidate_pin == "a84ff9cc2453ca91d581380de4b8b3f272f6f4be")' "$manifest" >/dev/null || fail 'Semgrep Rules comparison assertion failed'
jq -e '.codeql_pack_registry.root_count == 13 and (.codeql_pack_registry.roots | length) == 13 and any(.codeql_pack_registry.roots[]; .name == "codeql/swift-all" and .candidate == "6.8.4")' "$summary" >/dev/null || fail 'Swift CodeQL pack assertion failed'
jq -e '.codeql_pack_registry.roots[] | select(.name == "codeql/swift-queries" and .candidate == "1.3.11")' "$summary" >/dev/null || fail 'Swift query pack assertion failed'

manifest_names="$(jq -r '.targets[].name' "$manifest" | sort | tr '\n' ' ')"
summary_names="$(jq -r '.targets[].name' "$summary" | sort | tr '\n' ' ')"
[ "$manifest_names" = "$summary_names" ] || fail 'manifest and summary target sets differ'

printf 'PASS: %s requests, status counts, body/header digests, JSON bodies, target values, and evidence references verified\n' "$actual_count"

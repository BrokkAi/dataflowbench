#!/bin/bash
set -euo pipefail

DFB_SWIFT_ROOT="$(cd "$(dirname "$0")" && pwd)"
DFB_SWIFT_SOURCE="$DFB_SWIFT_ROOT/codeql-a7057b836bf29767461026718b14d20790b9085f"
DFB_SWIFT_DOWNLOADS="$DFB_SWIFT_ROOT/downloads"
mkdir -p "$DFB_SWIFT_DOWNLOADS" "$DFB_SWIFT_ROOT/compiler-prebuilt"

download_verify() {
  local name="$1" url="$2" expected_size="$3" expected_sha="$4"
  local output="$DFB_SWIFT_DOWNLOADS/$name" partial="$DFB_SWIFT_DOWNLOADS/$name.part"
  if [[ -e "$output" || -e "$partial" ]]; then
    printf 'Refusing to overwrite existing acquisition path: %s\n' "$output" >&2
    return 1
  fi
  curl --silent --show-error --fail --location --retry 3 --retry-delay 2 \
    --output "$partial" "$url"
  local got_size got_sha
  got_size="$(wc -c < "$partial" | tr -d '[:space:]')"
  got_sha="$(shasum -a 256 "$partial" | awk '{print $1}')"
  printf '%s size=%s sha256=%s\n' "$name" "$got_size" "$got_sha"
  if [[ "$got_size" != "$expected_size" || "$got_sha" != "$expected_sha" ]]; then
    printf 'Acquisition identity mismatch: %s\n' "$name" >&2
    return 1
  fi
  mv "$partial" "$output"
}

download_verify \
  swift-prebuilt-macos.tar.zst \
  https://media.githubusercontent.com/media/github/codeql/a7057b836bf29767461026718b14d20790b9085f/swift/third_party/resources/swift-prebuilt-macos.tar.zst \
  125119625 f5fddabc442a5c7664be4f022f09889177f420477060c1199eb714394987ad93
download_verify \
  resource-dir-macos.zip \
  https://media.githubusercontent.com/media/github/codeql/a7057b836bf29767461026718b14d20790b9085f/swift/third_party/resources/resource-dir-macos.zip \
  433044499 0589f8b61a87447d03b4b81b915f6b341ff8bcb123effda586cba46cc9487bd6
download_verify \
  bazel-9.0.0-darwin-arm64 \
  https://github.com/bazelbuild/bazel/releases/download/9.0.0/bazel-9.0.0-darwin-arm64 \
  60358731 2c3cce548a4b6a97a2a5267712187b784b52714c4a2b0613e7386b15669d783c
chmod 755 "$DFB_SWIFT_DOWNLOADS/bazel-9.0.0-darwin-arm64"

if [[ -n "$(/usr/bin/find "$DFB_SWIFT_ROOT/compiler-prebuilt" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  printf 'Refusing to extract into non-empty compiler-prebuilt directory\n' >&2
  exit 1
fi
/opt/homebrew/bin/zstd -d -c "$DFB_SWIFT_DOWNLOADS/swift-prebuilt-macos.tar.zst" \
  | /usr/bin/bsdtar -xf - -C "$DFB_SWIFT_ROOT/compiler-prebuilt"
cp "$DFB_SWIFT_SOURCE/swift/third_party/BUILD.swift-llvm-support.bazel" \
  "$DFB_SWIFT_ROOT/compiler-prebuilt/BUILD.bazel"

printf 'Verified assets and compiler-prebuilt override are ready.\n'

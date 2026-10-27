# CodeQL Swift source compatibility check

The official `github/codeql` ref `codeql-cli/v2.27.2` resolves through annotated tag object `ec7c65814286a8d4d35e5ee235f11adaf29068e3` to source commit **`a7057b836bf29767461026718b14d20790b9085f`**. The tag object says it is compatible with CLI 2.27.2, but GitHub reports the tag signature as unsigned (`verified: false`, reason `unsigned`). API responses are retained next to this file as `tag-ref.json` and `tag-object.json`.

The exact source tarball is retained at `execution-state/v092/swift-source/codeql-source-a7057b836bf29767461026718b14d20790b9085f.tar.gz` (51,480,263 bytes; SHA-256 `c737189f5f9f6a89eefabf2e82e6ecf9a2f866c4de2caf1f6407f69d143eae16`) and extracted to `execution-state/v092/swift-source/codeql-a7057b836bf29767461026718b14d20790b9085f/` (~505 MiB). The archive came from the commit-pinned codeload URL recorded below.

`adapters/codeql/swift-entry-extractor-v1/repair.patch` (SHA-256 `e7da7352a8b3a8e7679760e49e8f8abff05d7fa3e16007c7ed2987f49074f26a`) contains 19 files (305 insertions, 7 deletions). For the rebuild, it is applied to the exact source tree and verified against the untouched tar archive: every expected path is newly added or has a changed SHA-256, and isolated-repository reverse-check succeeds. The application log and per-file hashes are retained at `execution-state/v092/swift-source/patch-application/`. An initial nested-workdir `git apply` invocation reported success but made no changes; the final application uses `git apply --directory=execution-state/v092/swift-source/codeql-a7057b836bf29767461026718b14d20790b9085f` from the DataFlowBench worktree root. No analyzer or corpus run has started.

## Compatibility consequence

This source tree's `swift/ql/lib/qlpack.yml` declares `codeql/swift-all` **6.8.5** and `swift/ql/src/qlpack.yml` declares `codeql/swift-queries` 1.3.12. It pins Bazel 9.0.0, `rules_swift` 4.0.0-rc5-codeql.2, and the hermetic Swift 6.3.3 toolchain. Thus the patch applies cleanly, but the old `6.8.4-dfb.*` overlays, materializers and `queries/qlpack.yml` dependency are not a compatible latest-runtime path. A fresh lane must start from the 2.27.2/6.8.5 Swift pack, rebuild its generated schema/database scheme and QL outputs with the patched source, and give the derived pack a new version derived from 6.8.5. Reusing any 6.8.4 runtime would invalidate source/pack provenance.

## Assets and bounded build

The source's LFS pointers require these matching macOS Swift 6.3.3 assets for a reproducible tool build and runtime:

| Asset | Source-pinned URL suffix | Compressed size | SHA-256 |
| --- | --- | ---: | --- |
| `swift-prebuilt-macos.tar.zst` | `swift/third_party/resources/swift-prebuilt-macos.tar.zst` | 125,119,625 B | `f5fddabc442a5c7664be4f022f09889177f420477060c1199eb714394987ad93` |
| `resource-dir-macos.zip` | `swift/third_party/resources/resource-dir-macos.zip` | 433,044,499 B | `0589f8b61a87447d03b4b81b915f6b341ff8bcb123effda586cba46cc9487bd6` |

For either asset, prepend `https://media.githubusercontent.com/media/github/codeql/a7057b836bf29767461026718b14d20790b9085f/`. The two downloads total 558,164,124 B (~532 MiB); extracted resource footprint is larger. The extractor target directly depends on `//swift/third_party/resources:prebuilt`; the resource-dir archive is also needed to exercise the resulting analyzer runtime. Do not substitute older runtime/compiler outputs.

The bounded build target is `//swift/extractor:extractor.real`, using Bazel 9.0.0 (the archived macOS arm64 Bazel binary is 60,358,731 B, SHA-256 `2c3cce548a4b6a97a2a5267712187b784b52714c4a2b0613e7386b15669d783c`). The prior 2.27.1 source build took 102.67 s with a warm dependency/repository cache, two jobs, 4 GiB Bazel scheduler memory hint, 2 GiB JVM heap, and an 80,647,495,680-byte minimum free-space observation. That is historical diagnostic cost, not a 2.27.2 estimate. The execution plan retained a 40 GiB free-space floor, a 900 s timeout, disk polling, and one attempt.

## Fresh 2.27.2 build and package evidence

The exact patched 2.27.2 source completed the bounded `//swift/extractor:extractor.real` build in `execution-state/v092/swift-source/build-attempt-03/` (100.907 s, exit 0, 617,904 KiB observed peak RSS, 215,579,353,088-byte minimum free-space observation). Exact argv, environment, and result are in that attempt's `command.json` and `result.json`. The executable is 173,000,664 bytes, Mach-O x86_64, SHA-256 `593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f`.

The patched source also generated `swift/extractor/trap/generated/swift.dbscheme` using bounded `//swift/extractor/trap:generated_dbscheme` attempt 01 (22.650 s, exit 0). The generated schema is 56,113 bytes with SHA-256 `a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89`.

Official `//swift:install` attempt 01 completed in 163.429 s (exit 0) and installed the freshly built executable, generated schema, Swift 6.3.3 resource directory, and runtime dylibs. Its invocation/result/log are retained under `execution-state/v092/swift-source/extractor-pack-attempt-01/`. The installer initially wrote to `tools/swift-codeql/candidate-extractor`; that exact tree was moved without edits to `execution-state/v092/tools/swift-codeql/candidate-extractor/swift`. `candidate-extractor-relocation.json` records the original destination and pre/post inventory equality. The outer runtime has 2,277 files (1,724,779,338 bytes), no symlinks or external files, and is inventoried at `reports/releases/v0.9.2/acquisition/runtime-manifests/codeql-swift-extractor.json`; the legacy flat and mode-aware maps are `candidate-extractor-files.json` and `candidate-extractor-tree.json` in this directory.

Static wrapper inspection found that `tools/osx64/extractor` sets `DYLD_LIBRARY_PATH` to its own directory and execs sibling `extractor.real`; all `@rpath` dylib names are present beside the executable. One direct `@loader_path/../../../_solib_darwin_arm64/.../libswiftRemoteMirror.dylib` reference points to an absent `_solib_darwin_arm64` directory in the packaged runtime, while the dylib itself is present beside the executable and that directory is added to `DYLD_LIBRARY_PATH` by the wrapper. The Bazel runfiles copy is a set of symlinks into the Bazel cache and was not copied into the runtime.

A non-extracting launch through the relocated wrapper with only `-version` succeeded (exit 0, 39.111 s). It printed `Swift version 6.3.3 (swift-6.3.3-RELEASE)` and `Target: x86_64-apple-macosx28.0`; stderr was empty. The command supplied no source file or database path, and the full post-run pack inventory matched the retained tree manifest. Exact argv, allowlisted environment, stdout, stderr, exit status, and runtime hashes are retained in `qualification/codeql-swift-extractor/extractor-loader-attempt-01/`. This confirms dynamic loader startup for the version path; no analyzer or corpus run has started.

## Reproduction commands

Resolve and retain the official tag metadata, then acquire and unpack only the exact source archive:

```sh
gh api repos/github/codeql/git/ref/tags/codeql-cli/v2.27.2 > tag-ref.json
gh api repos/github/codeql/git/tags/ec7c65814286a8d4d35e5ee235f11adaf29068e3 > tag-object.json
curl -fL --retry 3 --retry-delay 2 \
  -o codeql-source-a7057b836bf29767461026718b14d20790b9085f.tar.gz \
  https://codeload.github.com/github/codeql/tar.gz/a7057b836bf29767461026718b14d20790b9085f
shasum -a 256 codeql-source-a7057b836bf29767461026718b14d20790b9085f.tar.gz
mkdir -p codeql-a7057b836bf29767461026718b14d20790b9085f
tar -xzf codeql-source-a7057b836bf29767461026718b14d20790b9085f.tar.gz \
  --strip-components=1 -C codeql-a7057b836bf29767461026718b14d20790b9085f
```

From the extracted source directory, the non-mutating applicability check is:

```sh
git -C /path/to/dataflowbench/execution-state/v092/swift-source/codeql-a7057b836bf29767461026718b14d20790b9085f apply --reverse --check --binary /path/to/dataflowbench/adapters/codeql/swift-entry-extractor-v1/repair.patch
```

The prior bounded build argv and CLT-specific environment are recorded in the portable evidence archive at `evidence/swift-entry-extractor-v1/portable-evidence.tar.gz` (`build-attempt-02/command.json` and `build-resources-plan.json`). Relocate all temporary paths before a future run; pin and verify the Bazel binary, fetch/verify the two source-revision LFS blobs, preserve the 40 GiB disk floor, and rebuild/revalidate the 6.8.5 packs before any analyzer controls.

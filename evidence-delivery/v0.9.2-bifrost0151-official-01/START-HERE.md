# Bifrost v0.15.1 delivery-copy package

## Snapshot inputs

This package contains lossless delivery copies of the 20 attempt directories listed by the series summary at `reports/releases/v0.9.2/execution-v6/bifrost-v0151-01/series-summary.json` (SHA-256 `bc01978c12a806d5db92494f3d306a4de8c86ab4d3f71d8c0c9ec7bf3f903376`). The summary records status `completed`, target `bifrost-v0151-01`, source commit `7f99684668065b8fb1ebc9b2852f058c64430647`, plan commit `515d9941978c12cafa37ba58eecacc0a4182226f`, and completion invocation `series-04-serial-fail-stop-1794023797838948000-96050`. These are input references for this copy; this package does not independently establish run qualification or publication readiness.

Each bundle manifest maps files back to its exact repository-relative source path and records the SHA-256 and byte count. Its `bundle.json` binds the manifest and compressed part digests. The exact per-file source-to-manifest audit and all bundle checks are recorded in `reports/releases/v0.9.2/review-handoff/bifrost-v0151-delivery-copy-check-01.json`.

Series04 attempt bundles:

- `bifrost-c-kernel-attempt-05-series-04` (`bifrost-c-kernel`): `detail/bifrost-c-kernel-attempt-05-series-04/`
- `bifrost-cpp-kernel-attempt-04-series-04` (`bifrost-cpp-kernel`): `detail/bifrost-cpp-kernel-attempt-04-series-04/`
- `bifrost-csharp-kernel-attempt-04-series-04` (`bifrost-csharp-kernel`): `detail/bifrost-csharp-kernel-attempt-04-series-04/`
- `bifrost-go-kernel-attempt-04-series-04` (`bifrost-go-kernel`): `detail/bifrost-go-kernel-attempt-04-series-04/`
- `bifrost-java-kernel-attempt-04-series-04` (`bifrost-java-kernel`): `detail/bifrost-java-kernel-attempt-04-series-04/`
- `bifrost-java-modeling-attempt-04-series-04` (`bifrost-java-modeling`): `detail/bifrost-java-modeling-attempt-04-series-04/`
- `bifrost-java-native-attempt-04-series-04` (`bifrost-java-native`): `detail/bifrost-java-native-attempt-04-series-04/`
- `bifrost-javascript-kernel-attempt-04-series-04` (`bifrost-javascript-kernel`): `detail/bifrost-javascript-kernel-attempt-04-series-04/`
- `bifrost-javascript-modeling-attempt-04-series-04` (`bifrost-javascript-modeling`): `detail/bifrost-javascript-modeling-attempt-04-series-04/`
- `bifrost-javascript-native-attempt-04-series-04` (`bifrost-javascript-native`): `detail/bifrost-javascript-native-attempt-04-series-04/`
- `bifrost-kotlin-kernel-attempt-04-series-04` (`bifrost-kotlin-kernel`): `detail/bifrost-kotlin-kernel-attempt-04-series-04/`
- `bifrost-php-kernel-attempt-04-series-04` (`bifrost-php-kernel`): `detail/bifrost-php-kernel-attempt-04-series-04/`
- `bifrost-python-kernel-attempt-04-series-04` (`bifrost-python-kernel`): `detail/bifrost-python-kernel-attempt-04-series-04/`
- `bifrost-python-modeling-attempt-04-series-04` (`bifrost-python-modeling`): `detail/bifrost-python-modeling-attempt-04-series-04/`
- `bifrost-python-native-attempt-04-series-04` (`bifrost-python-native`): `detail/bifrost-python-native-attempt-04-series-04/`
- `bifrost-ruby-kernel-attempt-04-series-04` (`bifrost-ruby-kernel`): `detail/bifrost-ruby-kernel-attempt-04-series-04/`
- `bifrost-rust-kernel-attempt-04-series-04` (`bifrost-rust-kernel`): `detail/bifrost-rust-kernel-attempt-04-series-04/`
- `bifrost-scala-kernel-attempt-04-series-04` (`bifrost-scala-kernel`): `detail/bifrost-scala-kernel-attempt-04-series-04/`
- `bifrost-smoke-attempt-06-series-04` (`bifrost-smoke`): `detail/bifrost-smoke-attempt-06-series-04/`
- `bifrost-typescript-kernel-attempt-04-series-04` (`bifrost-typescript-kernel`): `detail/bifrost-typescript-kernel-attempt-04-series-04/`

Additional retained Joern inputs are isolated under `joern108-retained/`:

- Original attempt: `reports/releases/v0.9.2/attempts/joern-swift-common108-attempt-05-series-02`
- Normal-attempt copy: `reports/releases/v0.9.2/normal/attempts/joern-swift-common108-attempt-05-series-02`
- Metadata projection inputs: `execution-state/v092/publication-evidence/joern108-metadata-projection-01` (six files)

## Copy totals

| Scope | Bundles | Files | Raw bytes | Compressed payload bytes | Parts |
|---|---:|---:|---:|---:|---:|
| Series04 attempts | 20 | 2287 | 24,524,088 | 2,303,611 | 20 |
| Retained Joern inputs | 3 | 3383 | 370,275,094 | 151,075,092 | 6 |
| Total | 23 | 5670 | 394,799,182 | 153,378,703 | 26 |

Compressed payload counts include each bundle's tar parts and compressed path manifest. The largest part is 41,943,040 bytes (40 MiB). All parts are at most 40 MiB.

## Verify and scope limits

Run `python3 scripts/evidence_bundle.py check <bundle-directory>` for each bundle directory under `detail/` and `joern108-retained/`. Full checks of all 23 bundles and path/hash/size comparisons against the current source directories passed. Originals remain in place. This records delivery integrity only; it makes no semantic-quality, benchmark-qualification, canonical-validation, or publication claim.

This snapshot includes only the 20 listed series04 attempt directories and the three explicit Joern scopes above. It excludes other historical attempts, controls bundles, ledgers, source/build outputs outside those exact scopes, and later validator, supervisor, or review-detail artifacts. Root-owned later artifacts need a separate addition to the package.

# Portable retained-control review tests

PR296 CI at afdc3105 and bb9e6284 failed because the retained schema-6 review test depended on eight ignored attempt-cache files and a locally installed macOS Bifrost executable. The exact base bff6e6ac2 does not contain this v0.9.2 test, so this is a feature test-fixture portability failure.

All eight original cache files were checked against the unchanged attempt02 artifact manifest: 56,573,952 bytes, exact sizes and SHA256s. The lossless evidence bundle stores five unique objects in a 496,203-byte LFS part. Its restore helper checks every fingerprint and full archive integrity, restores only absent cache paths without overwriting mismatches, and preserves existing matching files. No original cache, report, stream, manifest, qualification status or measurement is changed.

The unit test supplies only the recorded installed-binary hash as an identity witness at the exact recorded binary path. Every other manifest/stream/report digest and all original partial-discovery, obligation and proof assertions remain real. A wrong-binary-witness near miss still fails the unchanged production verifier. This is semantic unit testing against retained captures, **not** a fresh installed-binary check or runtime qualification. `scripts/review-v092-bifrost-controls.py` remains byte-identical.

Eight tests pass: the four original semantic tests plus clean-checkout restoration, no-overwrite, corrupt-archive rejection, and wrong-identity-witness rejection. The archive uses the existing independently tested lossless format and LFS detail-part rule. No analyzer invocation or benchmark retry occurred. Publication remains held.

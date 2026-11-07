# Historical Swift input copies

This small lossless archive contains the exact 96 historical raw JSON inputs
needed by native-control qualification. It contains no new analyzer results.
The original files, paths and hashes remain intact. The 431,729 payload bytes
compress to 57,839 bytes; the compressed part uses the existing Git LFS rule.

The member index is
`reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native06-archived-evidence-index-02.json`
(SHA-256 `9d4f9b105a0b936873cbd7ca578262b445a9aebeda8501583f56bf0d7bdf2e6e`).
It lists every original path, length and SHA-256, and binds the retained request05
whose input hashes predate the compact-history migration.

The reviewed native qualifier verifies the current commit's ordinary index,
historical request document and helper source; the exact Git LFS pointer; the
compressed bytes; the bounded single gzip/USTAR stream; all 96 regular members;
and the unchanged live original files. It does not extract files. Every other
source input still requires its direct current-commit Git blob. Historical raw
members remain absent from the ordinary Git tree.

This is an explicit storage indirection, not a claim that the raw JSON files are
ordinary blobs in the current commit or that the old source commit is a current
ancestor. A source-only preparation packet cannot qualify native controls,
the scored Joern cases, semantic quality or publication.

# Unpublished delivery preflight

The manifest retained here was prepared before the first website publication.
Local browser verification found that the preview server served the `.gz` index
URL with `Content-Encoding: gzip`, so Fetch decoded the archive rather than
returning its retained bytes. The canonical `20261113-v1` manifest changes only
that download URL to an opaque `.gz.bin` suffix. The original compressed input,
hashes, measured observations and qualification remain unchanged. This preflight
was never deployed; it is retained as a delivery attempt, not a publication.

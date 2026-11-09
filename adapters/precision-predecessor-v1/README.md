# Exact predecessor configuration inputs

These two files are byte-for-byte source snapshots from
`86092336d8f9ca32fe9e2c4042c2dced76c1feb1`, the green main revision preceding
the prospective precision templates. Their original logical paths and SHA-256
digests are pinned in `src/precision.rs` and tested against that Git revision.

Historical Swift reports hash their validator and adapter source as part of
the configuration closure. The new fixture inventory requires changes to
those files. Report validation can replay the old logical-path hash with these
exact predecessor bytes while continuing to hash every other query, model,
certificate and evidence file from its declared closure. A match is reported
as `Historical` with the source revision, not as current execution or new
qualification. Unknown versions, wrong stamps, modified snapshots, and other
configuration drift remain failures.

These files are retained configuration evidence, not executable adapters.

# Fixture provenance

Every case has `fixture_provenance` with `kind`, `origin`, `revision`, and
`license`. These fields are part of the public benchmark contract, not optional
metadata.

- `authored` fixtures identify `DataFlowBench` as origin, their introducing
  revision, and `MIT`.
- `imported` fixtures name the upstream project and immutable revision or
  release, retain the upstream license, and include any required notice files.
- Generated benchmark data, measurements, annotations, and ground truth are
  CC0-1.0; executable fixture programs and adapter code are MIT unless the
  imported material says otherwise.

Never copy third-party fixtures without this record. Preserve original notices
beside imported material and update its revision when the fixture changes.

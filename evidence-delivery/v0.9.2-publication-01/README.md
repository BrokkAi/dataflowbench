# Portable v0.9.2 publication inputs

This lossless LFS bundle carries only the selected release inputs: 4,252 raw
result artifacts, 92 exact canonical source reports and five additional
original Joern reports whose schema-only metadata lift remains mandatory.
It contains 4,349 files and 38,318,599 original bytes, compressed to 4,809,834
bytes including the manifest. The single data part is below 40 MiB.

The readable, reversible report/path map is
`reports/releases/v0.9.2/publication-v1/manifest.json`. Normalized publication
reports change only each row's raw-output path; no result, identity, diagnostic,
configuration or uncertainty is changed. Original evidence and ledger remain
intact. Delivery integrity is not semantic qualification or timing certification.

```sh
python3 -B scripts/v092_ledger_archive.py hydrate-current --root .
python3 -B scripts/v092_publication_evidence.py hydrate --root .
python3 -B scripts/v092_publication_evidence.py verify --root .
python3 -B scripts/v092_publication_evidence.py stage-site --root . --output docs/public/evidence/v0-9-2
```

Hydration checks all content digests before copying, refuses unknown or
nonidentical existing files, and never overwrites original evidence paths.
The staged static-site raw copies are ignored build output; Git retains the
compressed detailed archive rather than thousands of expanded artifacts.

# CodeQL adapter

The Java vertical-slice adapter creates one CodeQL database per canonical case,
compiles the fixture with its real `javac` build, runs the pinned
`dataflowbench/codeql-java` query pack, retains SARIF, and normalizes only the
presence or absence of query results. It does not treat query compilation,
database creation, or analysis failures as negative results.

The benchmark-controlled query identifies `dfb_source` call results as sources
and argument zero of `dfb_sink` calls as sinks. Canonical fixtures remain free
of CodeQL query syntax.

The adapter is pinned to `codeql/java-all@9.2.3`. With CodeQL CLI v2.26.3 and
the Java pack downloaded to an explicit directory, run:

```bash
codeql pack download --dir /path/to/codeql-packs codeql/java-all@9.2.3
cargo run -- run-codeql-java-vertical \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

Raw SARIF is retained under `reports/raw/codeql/`; the normalized report is
`reports/codeql-java-vertical.json`. Path evidence remains in SARIF, while
normalized `witness_checkpoints` stay empty until evidence locations can be
proven against canonical fixture markers.

## Retained v2.26.3 snapshot

The checked-in report uses CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/java-all@9.2.3`. All four positive cases are `reached` and all four
negative cases are `not-reached`. Each case uses an isolated cold database; no
database or compiled fixture is reused across the pair. The adapter removes
temporary databases and workspaces after retaining SARIF.

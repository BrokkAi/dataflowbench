# CodeQL adapter

The Java kernel adapter creates one CodeQL database per canonical case,
compiles the fixture with its real `javac` build, runs the pinned
`dataflowbench/codeql-java` query pack, retains SARIF, and normalizes only the
presence or absence of query results. It does not treat query compilation,
database creation, or analysis failures as negative results.

The benchmark-controlled query identifies the kernel's canonical source call
results and sink argument zero. Canonical fixtures remain free of CodeQL query
syntax.

The adapter is pinned to `codeql/java-all@9.2.3`. With CodeQL CLI v2.26.3 and
the Java pack downloaded to an explicit directory, run:

```bash
codeql pack download --dir /path/to/codeql-packs codeql/java-all@9.2.3
cargo run -- run-codeql-java-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

Raw SARIF is retained under `reports/raw/codeql/`; the normalized report is
`reports/codeql-java-kernel.json`. Path evidence remains in SARIF, while
normalized `witness_checkpoints` stay empty until evidence locations can be
proven against canonical fixture markers.

## Retained v2.26.3 snapshot

The checked-in report uses CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/java-all@9.2.3`. Of 32 assertions, 15 are `reached` and 17 are
`not-reached`; 27 match their expected polarity. The expression, alias, and
exception positives are false negatives, while the array-element and loop-kill
negatives are false positives. Each case uses an isolated cold database; no
database or compiled fixture is reused across the pair. The adapter removes
temporary databases and workspaces after retaining SARIF.

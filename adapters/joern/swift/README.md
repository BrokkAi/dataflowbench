# Compiler-backed Swift adapter

The Swift adapter has its own query, model declarations, activation certificate,
preregistered partition, recorder and report paths. It does not change the
historical Joern kernel or modeling configuration hashes.

See [the Swift Joern contract and reproduction record](../../../docs/joern-swift.md)
for exact pins, native identity activation, budgets, capability boundaries and
commands. `activation.json` binds 36 independent native controls;
`partition.json` preserves all 90 applicable assertions, including six
predeclared unsupported modeling assertions. Calibration remains unscored.

`query.sc` requires compiler-derived method identities and native callee edges.
`inspect.sc` is the non-scored native-identity diagnostic used during activation.
No source-text resolver, graph repair, fixture rewrite, or analyzer fork is used.

Native query observations are provisional. Missing exact bindings fail closed;
aggregate memory uncertainty and bounded-engine absence stay inconclusive.
These files establish adapter execution, not a release or publication.

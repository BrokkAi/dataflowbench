# Resolved Swift process-input diagnostic profile

This explicit **adapter-corrected** profile adds environment and argument
collection sources to CodeQL CLI 2.27.1 / `codeql/swift-all` 6.8.4. Vendor source,
barrier, and additional-flow definitions remain intact. Vendor flow is run
separately without these additions. The sink predicate is a byte-identical copy
of the verified `swift-foundation-identity-v1` profile, checked by the verifier.

`FoundationSources.qll` binds the resolved property declaration, its nominal
owner and module, collection element types, accessor, and property-getter
control-flow node. The source is the getter's returned collection value:

- `Foundation.ProcessInfo.environment`: instance receiver and getter self type
  must resolve to `Foundation.ProcessInfo`; key and value types are Swift String.
- `Swift.CommandLine.arguments`: the getter must be static, its access base a
  metatype, and the collection element type Swift String.

The flow query adds these source nodes to the shipped sources, uses the
corrected Foundation sinks, and otherwise retains vendor flow semantics. It
adds no indexing, text-matching, or wrapper-based propagation rule. Missing
identity or getter information fails closed. Empty output does not establish
complete or clean analysis.

`roles.ql` reports the added source roles, shipped source roles, and both sink
profiles. `flow.ql` reports actual flows under each profile. `identity.ql`
retains declaration/type diagnostics; display strings are diagnostic output,
not production matching criteria.

See [the evidence and limits](../../../docs/swift-foundation-sources-profile.md).
No scored population or historical vendor-native result is changed.

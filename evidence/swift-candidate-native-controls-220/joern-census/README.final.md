# Final bounded result

The complete census finished against the already acquired Joern 4.0.633
candidate. The archive SHA-256 is
`e11563c7cf4797db76655524398f108c3469a518fa3ed823de0aac2a1155aec6`.

Counts are in `result.json` and `summary.json`. The inventory is complete for
the extracted candidate: every extracted file has a size and SHA-256; every
JAR path is mapped to a JAR SHA-256; every unique JAR content has all members,
resources, and class-member hashes. Duplicate JAR paths are not re-expanded.

Typed API inspection observed `DefaultSemantics -> FullNameSemantics`,
`Semantics.forMethod(Method) -> Option[FlowSemantic]`, and the shipped generic
`atoi` C mapping. It found no typed Swift Foundation native role-binding API.
That is the concrete qualification blocker. No Joern runtime was launched and
no unsupported or absence result was inferred.

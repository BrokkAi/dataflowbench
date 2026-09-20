The positive control did not fire, and this file says so rather than leaving
the attempt out.

What was tried: the exact flow the shipped policy names — a jakarta.servlet
`HttpServletRequest.getParameter(String)` value concatenated into SQL text and
passed to `java.sql.Statement.execute(String)` — in a Maven project declaring
the real `jakarta.servlet:jakarta.servlet-api:6.1.0` dependency, which the scan
report shows the CLI selecting as a dependency pack. This is the one retained
and reproducible positive-control attempt; no unretained manual variants are
used as evidence.

What the tool said. On every one of those shapes the run came back
`inconclusive (partial_discovery)` with

    taint selector did not execute completely: selector
    `/analysis/sources/entries/servlet-request-parameter/selector` could not
    prove an empty row selection (calls: semantic_analysis_partial:
    call_bindings did not establish complete actual-to-formal coverage
    (dispatch outcome=unknown, coverage=open, target_count=1,
    binding coverage=unknown))

and with the JVM external-model pack `bifrost.external.java` reported
`incompatible` — "complete activation evidence does not satisfy the manifest and
shard selector". The policy declares `:proof exact` on both endpoint selectors
and the catalog lists `exact-call-target` and `semantic-model-provenance` among
its required capabilities, so an unproven dispatch is refused rather than
guessed. That is the policy behaving as its own description promises; what this
probe could not do on this host is assemble a project in which the proof is
available.

Why the declines do not rest on it. This control is the weaker of two available
liveness arguments, and the stronger one is in the sweep itself. On all
thirty-six tool-native fixtures the same policy comes back
`completion: complete` with its own `empty_selection` notes naming it by id and
saying, in the tool's words, that it "bound no source endpoint ... so this run
reports zero findings VACUOUSLY rather than proving that no flow exists". A
policy that failed to load could not produce those. The partition rows below are
decided on the endpoint identities the policy DECLARES — read verbatim out of
the pinned executable, in `security-policy-source.rqlp` — and on that measured
vacuity, neither of which needs the control.

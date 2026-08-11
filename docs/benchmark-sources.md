# Benchmark sources

External suites are inputs to scenario design and real-project confirmation;
they are not copied into the scored core without provenance and review.

- [xAST](https://github.com/alipay/ant-application-security-testing-benchmark)
  provides the closest cross-language semantic matrix. Its context, flow,
  field, object, path, and language-feature scenarios are useful design inputs.
- [Joern's frontend data-flow tests](https://github.com/joernio/joern/tree/master/joern-cli/frontends)
  provide compact Java, JavaScript, Python, and other language regressions.
  Tool-owned tests are donors, not independent ground truth.
- [OpenTaint](https://github.com/seqra/opentaint) provides JVM samples and
  regressions for aliases, virtual calls, access paths, summaries, and taint
  rules. It is evaluated as a tool rather than treated as a benchmark authority.
- [OWASP Benchmark](https://owasp.org/www-project-benchmark/) provides
  executable positive and negative vulnerability cases for Java and Python.
- [SecBench.js](https://github.com/cristianstaicu/SecBench.js) provides vetted,
  executable real-world Node.js vulnerabilities.
- [CWE-Bench-Java](https://github.com/iris-sast/cwe-bench-java) provides pinned
  buggy and fixed revisions of real Java vulnerabilities.
- [TaintBench](https://taintbench.github.io/) demonstrates careful case-level
  source/sink configuration and real-world Android evaluation methodology.
- [NIST Juliet](https://samate.nist.gov/SARD/test-suites/112) provides broad
  paired synthetic variants, but its scale and repetition require curation.

Imported fixtures retain the upstream license and immutable revision described
in [fixture provenance](fixture-provenance.md).

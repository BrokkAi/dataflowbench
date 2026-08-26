/**
 * @name DataFlowBench JavaScript taint-modeling matrix
 * @description Encodes the benchmark-controlled model declarations of docs/modeling-matrix.md natively in a CodeQL data-flow configuration, and reports flow that those declarations — rather than the fixture bodies — imply.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/javascript-taint-modeling
 * @tags security
 */

import javascript

/**
 * The modeling matrix is restricted to `.js` fixtures for the same reason the
 * kernel query is: the CodeQL JavaScript library also extracts TypeScript, and
 * a future TypeScript modeling population must not silently share this query's
 * result set.
 */
predicate isJavaScriptFixture(DataFlow::Node node) { node.getFile().getExtension() = "js" }

/**
 * The store a persistence-boundary call's receiver denotes.
 *
 * Store identity is the receiver's *binding*, not its data-flow source node:
 * `Store.put` and `Store.get` sit in two different procedures by construction,
 * so each reference has its own local source even when both denote the same
 * store. Comparing the bound variable is what makes template 11's type-level
 * `store: primary` and template 12's receiver-level store identity one
 * relation — a static call's receiver is the class binding, an instance call's
 * receiver is the instance binding, and `alpha` and `beta` are two bindings.
 */
Variable storeIdentity(DataFlow::CallNode call) {
  result = call.getReceiver().asExpr().(VarAccess).getVariable()
}

/**
 * The benchmark's model declarations, encoded in the surface
 * `adapters/codeql/README.md` states as this adapter's design: the query owns
 * the CodeQL model and the case metadata stays analyzer neutral.
 *
 * Every predicate below is a transcription of a declaration in
 * docs/modeling-matrix.md#the-twelve-templates — an entity identity, a role,
 * and a binding — and nothing else. There is no per-case, per-template, or
 * per-polarity branching: all six categories are declared at once and each
 * fixture contains only the entities its own template names. The undeclared
 * siblings the negatives turn on — `fetchLocal`, `discard`, `block`, `hold`,
 * `sanitize`, `onIgnored`, `onUndeclared` — appear nowhere here, which is what
 * makes the negatives measure identity binding rather than name shape.
 */
module DataFlowBenchModelingConfig implements DataFlow::ConfigSig {
  /**
   * Category S, template 1: `Config.fetchRemote`, role `source`, `out: return`;
   * plus the benchmark input `dfb_source` every other template begins from.
   *
   * Category E, templates 9 and 10: `Handler.onRequest` and
   * `Handler.onDeclared`, role `entry-point`, `in: 0` tainted on entry. CodeQL
   * does not require a source to be reachable from a call-graph root, so
   * naming the parameter node of an uncalled method is the whole of the
   * entry-root synthesis this category asks for. Selectivity is the identity
   * test in the predicate body.
   */
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = ["dfb_source", "fetchRemote"] and
      source = call and
      isJavaScriptFixture(source)
    )
    or
    exists(Function handler |
      handler.getName() = ["onRequest", "onDeclared"] and
      source = DataFlow::parameterNode(handler.getParameter(0)) and
      isJavaScriptFixture(source)
    )
  }

  /**
   * Category S, template 2: `Audit.record`, role `sink`, `in: 0`; plus the
   * benchmark sink `dfb_sink`.
   */
  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = ["dfb_sink", "record"] and
      sink = call.getArgument(0) and
      isJavaScriptFixture(sink)
    )
  }

  /**
   * Category Z, templates 5 and 6: `Clean.scrub`, role `sanitizer`, `in: 0`.
   *
   * The barrier sits on the declared input position, which is exactly what
   * "taint arriving at the named input position does not leave the entity at
   * any position" means. `scrub`'s body is the identity function, so an engine
   * that read the body would carry the taint through; only the declaration
   * stops it.
   */
  predicate isBarrier(DataFlow::Node node) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "scrub" and
      node = call.getArgument(0) and
      isJavaScriptFixture(node)
    )
    or
    // The explicit **no-flow** declarations of templates 3 and 7. `Opaque.block`
    // is declared as not propagating and `Bridge.hold` carries an explicit
    // no-flow summary; both bodies are byte-identical to their declared
    // siblings', so absence alone would not state the declaration — CodeQL
    // reads a body it can see, and for `hold` it does. A summary model is an
    // instruction to produce the summarized semantics whether or not the body
    // was read, and the no-flow summary is what this clause states.
    exists(DataFlow::CallNode call |
      call.getCalleeName() = ["block", "hold"] and
      node = call.getArgument(0) and
      isJavaScriptFixture(node)
    )
  }

  predicate isAdditionalFlowStep(DataFlow::Node node1, DataFlow::Node node2) {
    // Category P, template 3: `Opaque.carry`, role `propagator`, in: 0, out:
    // return. The body routes through a reflective self-dispatch that no
    // engine in the v0.4.0 freeze follows, so this step is the only route.
    // `Opaque.block` carries an identical body and is deliberately undeclared.
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "carry" and
      node1 = call.getArgument(0) and
      node2 = call and
      isJavaScriptFixture(node1)
    )
    or
    // Category P, template 4: `Opaque.select`, role `propagator`, in: 1, out:
    // return. Positional fidelity is native — the step names argument 1
    // specifically, and argument 0 is not mapped.
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "select" and
      node1 = call.getArgument(1) and
      node2 = call and
      isJavaScriptFixture(node1)
    )
    or
    // Category O, template 7: `Bridge.pass`, role `summary`, in: 0, out:
    // return. `Bridge.hold` carries an explicit no-flow summary, so it is
    // declared by being absent from this predicate even though its body — the
    // identity function, byte-identical to `pass`'s — says otherwise.
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "pass" and
      node1 = call.getArgument(0) and
      node2 = call and
      isJavaScriptFixture(node1)
    )
    or
    // Category O, template 8: `Bridge.deposit`, role `summary`, in: 0, out:
    // `1.payload`. The summary's output position is a heap location, so the
    // step lands on reads of the declared property off the object that flowed
    // into argument 1. `deposit`'s body writes nothing at all, so the field's
    // contents come from this declaration or from nowhere; the sibling
    // property `spare` is not named here, which is what the negative turns on.
    exists(DataFlow::CallNode call, DataFlow::PropRead read |
      call.getCalleeName() = "deposit" and
      read.getPropertyName() = "payload" and
      read.getBase().getALocalSource() = call.getArgument(1).getALocalSource() and
      node1 = call.getArgument(0) and
      node2 = read and
      isJavaScriptFixture(node1)
    )
    or
    // Category B, templates 11 and 12: `Store.put`, role `store-write`, in: 1,
    // key: 0; and `Store.get`, role `store-read`, out: return, key: 0, sharing
    // one store identity. The pair links only when the two calls agree on the
    // constant key *and* on the store the receiver denotes — which is the
    // type-level `store: primary` of template 11 (both calls address the class
    // itself) and the receiver-level `store: <receiver identity>` of template
    // 12 (both calls address the same instance) in one relation. `put` and
    // `get` have empty bodies; the roundtrip exists only in this declaration.
    exists(DataFlow::CallNode put, DataFlow::CallNode get |
      put.getCalleeName() = "put" and
      get.getCalleeName() = "get" and
      put.getArgument(0).getStringValue() = get.getArgument(0).getStringValue() and
      storeIdentity(put) = storeIdentity(get) and
      node1 = put.getArgument(1) and
      node2 = get and
      isJavaScriptFixture(node1)
    )
  }
}

module DataFlowBenchModelingFlow = TaintTracking::Global<DataFlowBenchModelingConfig>;

import DataFlowBenchModelingFlow::PathGraph

from DataFlowBenchModelingFlow::PathNode source, DataFlowBenchModelingFlow::PathNode sink
where DataFlowBenchModelingFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "A benchmark-declared source reaches a benchmark-declared sink."

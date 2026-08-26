/**
 * @name DataFlowBench Python taint-modeling matrix
 * @description Encodes the twelve benchmark-controlled model declarations of
 *              docs/modeling-matrix.md natively, as one `DataFlow::ConfigSig`.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/python-taint-modeling
 * @tags security
 */

private import python
import semmle.python.dataflow.new.DataFlow
import semmle.python.dataflow.new.TaintTracking

// The analyzer-neutral declarations of `docs/modeling-matrix.md`, encoded in
// the surface `adapters/codeql/README.md` records as this adapter's own: the
// query owns the CodeQL model, and the case metadata stays analyzer neutral.
//
// Entity identity is a type-or-module plus a member plus, where the role needs
// it, a parameter position counted from `0`. Python spells the twelve
// declaring types as the fixture module that carries them, so a declaration
// binds to the member name inside that module. Two rules keep the binding
// honest: a member is matched by its own identifier, never by a name shape,
// and the undeclared sibling of every pair (`fetch_local`, `discard`,
// `sanitize`, `on_ignored`, `on_undeclared`) appears nowhere below.

/** A call written as a bare name, e.g. `carry(v)`. */
private DataFlow::CallCfgNode namedCall(string name) {
  result.getFunction().asCfgNode().(NameNode).getId() = name
}

/** A call written as a member of `receiver`, e.g. `alpha.put(k, v)`. */
private DataFlow::CallCfgNode memberCall(string name, string receiver) {
  exists(Attribute attribute |
    attribute = result.getFunction().asExpr() and
    attribute.getName() = name and
    receiver = attribute.getObject().(Name).getId()
  )
}

/** The text of a constant string argument, used for the store key. */
private string constantKey(DataFlow::Node node) {
  result = node.asExpr().(StringLiteral).getText()
}

module DataFlowBenchModeling implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    // The benchmark's own controlled input, on every template whose source is
    // not itself a declared entity.
    source = namedCall("dfb_source")
    or
    // Template 1 — `source`, `out: return`, on module `config` member
    // `fetch_remote`. The sibling `fetch_local` is deliberately absent.
    source = namedCall("fetch_remote")
    or
    // Templates 9 and 10 — `entry-point`, `in: 0` tainted on entry, on module
    // `handler` members `on_request` and `on_declared`. Nothing in either
    // fixture calls them; CodeQL's data flow does not require a source to be
    // reachable from a call-graph root, so the parameter node is a root on its
    // own. Selectivity is the identity test in this disjunct: the undeclared
    // siblings `on_ignored` and `on_undeclared` are not named.
    exists(Function handler |
      handler.getName() = ["on_request", "on_declared"] and
      source = DataFlow::parameterNode(handler.getArg(0))
    )
  }

  predicate isSink(DataFlow::Node sink) {
    // The benchmark's own sink, on every template whose sink is not itself a
    // declared entity.
    sink = namedCall("dfb_sink").getArg(0)
    or
    // Template 2 — `sink`, `in: 0`, on module `audit` member `record`. The
    // sibling `discard` is deliberately absent.
    sink = namedCall("record").getArg(0)
  }

  predicate isBarrier(DataFlow::Node node) {
    // Templates 5 and 6 — `sanitizer`, `in: 0`, on module `clean` member
    // `scrub`. `scrub`'s body is the identity function, so the barrier, not
    // the body, is what suppresses the flow. The sibling `sanitize` is
    // deliberately absent: template 6's positive must still be reported.
    node = namedCall("scrub").getArg(0)
    or
    // Template 3's explicit no-flow declaration for `block`, and template 7's
    // explicit no-flow summary for `hold`. Both siblings carry bodies
    // identical to their declared counterparts, so without these clauses the
    // body — not the declaration — would decide the negative.
    node = namedCall("block").getArg(0)
    or
    node = namedCall("hold").getArg(0)
  }

  predicate isAdditionalFlowStep(DataFlow::Node node1, DataFlow::Node node2) {
    // Template 3 — `propagator`, `in: 0`, `out: return`, on module `opaque`
    // member `carry`. The body is a reflective self-dispatch resolved from a
    // run-time string, which no pinned engine follows, so this step is the
    // only route from the argument to the result.
    exists(DataFlow::CallCfgNode call |
      call = namedCall("carry") and node1 = call.getArg(0) and node2 = call
    )
    or
    // Template 4 — `propagator`, `in: 1`, `out: return`, on module `opaque`
    // member `select`. Position 1 is named specifically; taint at position 0
    // gets no step.
    exists(DataFlow::CallCfgNode call |
      call = namedCall("select") and node1 = call.getArg(1) and node2 = call
    )
    or
    // Template 7 — `summary`, `in: 0`, `out: return`, on module `bridge`
    // member `pass_through`.
    exists(DataFlow::CallCfgNode call |
      call = namedCall("pass_through") and node1 = call.getArg(0) and node2 = call
    )
    or
    // Template 8 — `summary`, `in: 0`, `out: 1.payload`, on module `bridge`
    // member `deposit`. The output position is a heap location, so the step
    // lands on the read of the declared attribute of the declared argument.
    // `deposit`'s body writes nothing; the attribute's contents come from this
    // declaration or from nowhere, and the sibling attribute `spare` gets no
    // step.
    exists(DataFlow::CallCfgNode call, Attribute read |
      call = namedCall("deposit") and
      node1 = call.getArg(0) and
      read.getName() = "payload" and
      read.getObject().(Name).getId() = call.getArg(1).asExpr().(Name).getId() and
      read.getScope() = call.getScope() and
      node2.asExpr() = read
    )
    or
    // Templates 11 and 12 — `store-write` (`in: 1`, `key: 0`) and `store-read`
    // (`out: return`, `key: 0`) on type `Store` members `put` and `get`,
    // sharing one store identity. The identity is the receiver, which covers
    // both templates: template 11's receiver is the type itself and template
    // 12's is the instance. The roundtrip closes only when the store identity
    // and the constant key both agree, which is what the two negatives
    // separate — distinct keys in template 11, distinct instances in template
    // 12.
    exists(DataFlow::CallCfgNode write, DataFlow::CallCfgNode read, string store |
      write = memberCall("put", store) and
      read = memberCall("get", store) and
      constantKey(write.getArg(0)) = constantKey(read.getArg(0)) and
      node1 = write.getArg(1) and
      node2 = read
    )
  }
}

module DataFlowBenchModelingFlow = TaintTracking::Global<DataFlowBenchModeling>;

from DataFlow::Node source, DataFlow::Node sink
where DataFlowBenchModelingFlow::flow(source, sink)
select sink.getLocation(), "A benchmark-declared source reaches a benchmark-declared sink."

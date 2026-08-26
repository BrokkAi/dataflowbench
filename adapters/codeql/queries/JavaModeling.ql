/**
 * @name DataFlowBench Java taint-modeling matrix
 * @description Encodes the twelve benchmark-supplied model declarations of
 *              docs/modeling-matrix.md natively in CodeQL's data-flow
 *              configuration surface, for the Java modeling population.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/java-taint-modeling
 * @tags security
 */

import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.dataflow.TaintTracking

/**
 * Entity identity, as the model declaration language defines it: a declaring
 * type plus a member name. Binding is never by name shape and never by a
 * substring, so `Audit.record` says nothing about `Audit.discard`.
 */
predicate modelCall(MethodCall call, string type, string member) {
  call.getMethod().getDeclaringType().getName() = type and
  call.getMethod().getName() = member
}

/** The string constant a store call is keyed by. */
predicate storeKey(MethodCall call, string key) {
  call.getArgument(0).(CompileTimeConstantExpr).getStringValue() = key
}

/**
 * Whether two store calls address the same store identity.
 *
 * Template 11 binds the store to the type: `Store.put` and `Store.get` are
 * static, so neither call carries an instance receiver — a static call's
 * qualifier is the `TypeAccess`, never a variable. Template 12 binds it to the
 * receiver instance, so the two calls must name the same variable.
 */
predicate sameStore(MethodCall put, MethodCall get) {
  put.getQualifier().(VarAccess).getVariable() = get.getQualifier().(VarAccess).getVariable()
  or
  not put.getQualifier() instanceof VarAccess and not get.getQualifier() instanceof VarAccess
}

module DataFlowBenchModelingConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    // The benchmark's own canonical source. Every fixture that is not itself a
    // declared-source assertion starts here.
    exists(MethodCall call |
      call.getMethod().getName() = "dfb_source" and
      source.asExpr() = call
    )
    or
    // Template 1 — role `source`, entity `Config.fetchRemote`, out: return.
    // The undeclared sibling `Config.fetchLocal` is deliberately absent.
    exists(MethodCall call |
      modelCall(call, "Config", "fetchRemote") and
      source.asExpr() = call
    )
    or
    // Templates 9 and 10 — role `entry-point`, entities `Handler.onRequest`
    // and `Handler.onDeclared`, in: 0 tainted on entry. Neither method is
    // called from anywhere in its fixture; CodeQL's data flow does not require
    // a source to be reachable from a call-graph root. The undeclared siblings
    // `onIgnored` and `onUndeclared` are deliberately absent.
    exists(Method handler |
      handler.getDeclaringType().getName() = "Handler" and
      handler.getName() = ["onRequest", "onDeclared"] and
      source.asParameter() = handler.getParameter(0)
    )
  }

  predicate isSink(DataFlow::Node sink) {
    // The benchmark's own canonical sink.
    exists(MethodCall call |
      call.getMethod().getName() = "dfb_sink" and
      sink.asExpr() = call.getArgument(0)
    )
    or
    // Template 2 — role `sink`, entity `Audit.record`, in: 0. The undeclared
    // sibling `Audit.discard` is deliberately absent.
    exists(MethodCall call |
      modelCall(call, "Audit", "record") and
      sink.asExpr() = call.getArgument(0)
    )
  }

  predicate isBarrier(DataFlow::Node node) {
    // Templates 5 and 6 — role `sanitizer`, entity `Clean.scrub`, in: 0.
    // `Clean.sanitize` is a sibling with the same identity body and a name at
    // least as sanitizer-shaped, and it is not declared.
    exists(MethodCall call |
      modelCall(call, "Clean", "scrub") and
      node.asExpr() = call.getArgument(0)
    )
    or
    // The explicit no-flow declarations the model language allows where a tool
    // has one: template 3's `Opaque.block` and template 7's `Bridge.hold`.
    // Both bodies say flow — `hold`'s is the identity function — so without
    // these clauses the query would report the body's semantics rather than
    // the summary's, which is exactly the distinction category O exists to
    // make observable.
    exists(MethodCall call |
      modelCall(call, "Opaque", "block") and
      node.asExpr() = call.getArgument(0)
    )
    or
    exists(MethodCall call |
      modelCall(call, "Bridge", "hold") and
      node.asExpr() = call.getArgument(0)
    )
  }

  predicate isAdditionalFlowStep(DataFlow::Node node1, DataFlow::Node node2) {
    // Template 3 — role `propagator`, entity `Opaque.carry`, in: 0, out: return.
    exists(MethodCall call |
      modelCall(call, "Opaque", "carry") and
      node1.asExpr() = call.getArgument(0) and
      node2.asExpr() = call
    )
    or
    // Template 4 — role `propagator`, entity `Opaque.select`, in: 1, out: return.
    // Positional fidelity is native: the step names argument 1 specifically, so
    // taint at the undeclared position 0 never takes it.
    exists(MethodCall call |
      modelCall(call, "Opaque", "select") and
      node1.asExpr() = call.getArgument(1) and
      node2.asExpr() = call
    )
    or
    // Template 7 — role `summary`, entity `Bridge.pass`, in: 0, out: return.
    exists(MethodCall call |
      modelCall(call, "Bridge", "pass") and
      node1.asExpr() = call.getArgument(0) and
      node2.asExpr() = call
    )
    or
    // Template 8 — role `summary`, entity `Bridge.deposit`, in: 0,
    // out: `1.payload`. The output position is a heap location, so the step
    // lands on the reads of that field of that object rather than on a return
    // value. `deposit`'s body writes nothing, so the field's contents come
    // from this declaration or from nowhere, and the sibling field `spare`
    // takes no step.
    exists(MethodCall call, FieldRead read |
      modelCall(call, "Bridge", "deposit") and
      read.getField().getName() = "payload" and
      read.getQualifier().(VarAccess).getVariable() =
        call.getArgument(1).(VarAccess).getVariable() and
      node1.asExpr() = call.getArgument(0) and
      node2.asExpr() = read
    )
    or
    // Templates 11 and 12 — roles `store-write` and `store-read` sharing one
    // store identity. `Store.put` binds in: 1 under key: 0; `Store.get` binds
    // out: return under key: 0. The two close a roundtrip only when the key
    // constants agree and the store identities agree, which is what the
    // field-separation and object-separation negatives test.
    exists(MethodCall put, MethodCall get, string key |
      modelCall(put, "Store", "put") and
      modelCall(get, "Store", "get") and
      storeKey(put, key) and
      storeKey(get, key) and
      sameStore(put, get) and
      node1.asExpr() = put.getArgument(1) and
      node2.asExpr() = get
    )
  }
}

module DataFlowBenchModelingFlow = TaintTracking::Global<DataFlowBenchModelingConfig>;

import DataFlowBenchModelingFlow::PathGraph

from DataFlowBenchModelingFlow::PathNode source, DataFlowBenchModelingFlow::PathNode sink
where DataFlowBenchModelingFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "A benchmark-declared model carried input to the declared sink."

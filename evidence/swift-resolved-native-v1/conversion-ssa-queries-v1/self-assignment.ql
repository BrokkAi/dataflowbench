/** @name Resolved self assignment and SSA return linkage
 * @kind table
 * @id dfb/swift-self-assignment-linkage
 */
import FoundationSources
import codeql.swift.dataflow.Ssa
import codeql.swift.dataflow.internal.DataFlowPrivate as Native
from AssignExpr assign, DataFlow::Node input, string destination, boolean hasWrite,
 boolean rhsToDefinition, boolean definitionToReturn, boolean rhsToReturn
where assign.getLocation().getFile().getBaseName() = "main.swift" and
 assign.getDest().(DeclRefExpr).getDecl() instanceof SelfParamDecl and input.asExpr() = assign.getSource() and
 destination = assign.getDest().(DeclRefExpr).getDecl().toString() and
 (if exists(Ssa::WriteDefinition def | def.assigns(input.getCfgNode())) then hasWrite = true else hasWrite = false) and
 (if exists(DataFlow::Node d, Ssa::WriteDefinition def | d.asDefinition()=def and def.assigns(input.getCfgNode()) and DataFlow::localFlowStep(input,d)) then rhsToDefinition=true else rhsToDefinition=false) and
 (if exists(DataFlow::Node d, Ssa::WriteDefinition def, Native::ReturnNode ret | d.asDefinition()=def and def.assigns(input.getCfgNode()) and DataFlow::localFlowStep(d,ret)) then definitionToReturn=true else definitionToReturn=false) and
 (if exists(Native::ReturnNode ret | DataFlow::localFlow(input,ret)) then rhsToReturn=true else rhsToReturn=false)
select assign.getLocation().getStartLine(), destination, hasWrite, rhsToDefinition, definitionToReturn, rhsToReturn

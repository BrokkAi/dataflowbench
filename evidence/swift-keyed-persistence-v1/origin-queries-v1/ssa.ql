/** @name Diagnose suite receiver SSA writes and reads
 * @kind table
 * @id dfb/swift-suite-ssa
 */
import FoundationSources
import codeql.swift.dataflow.Ssa
from Ssa::WriteDefinition definition, ControlFlowNode value, ControlFlowNode read
where definition.assigns(value) and read=definition.getARead() and value.getLocation().getFile().getBaseName()="main.swift"
select value.getLocation().getStartLine(),value.getLocation().getStartColumn(),value.getAst().getAPrimaryQlClass(),read.getLocation().getStartLine(),read.getLocation().getStartColumn(),read.getAst().getAPrimaryQlClass()

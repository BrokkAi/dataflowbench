/** @name Diagnose suite receiver SSA writes and reads
 * @kind table
 * @id dfb/swift-suite-ssa
 */
import FoundationSources
import codeql.swift.dataflow.Ssa
import codeql.swift.controlflow.CfgNodes
from Ssa::WriteDefinition definition, CfgNode value, CfgNode read
where definition.assigns(value) and read=definition.getARead() and value.getLocation().getFile().getBaseName()="main.swift"
select value.getLocation().getStartLine(),value.getLocation().getStartColumn(),value.getAst().getAPrimaryQlClass(),read.getLocation().getStartLine(),read.getLocation().getStartColumn(),read.getAst().getAPrimaryQlClass()

/** @name SSA definition proof availability
 * @kind table
 * @id dfb/swift-suite-definitions
 */
import FoundationSources
import codeql.swift.dataflow.Ssa
import codeql.swift.controlflow.CfgNodes
from Ssa::Definition definition, VarDecl variable, boolean write
where variable=definition.getSourceVariable().asVarDecl() and variable.getLocation().getFile().getBaseName()="main.swift" and
 (if definition instanceof Ssa::WriteDefinition then write=true else write=false)
select variable.getName(),write,count(CfgNode value | definition.(Ssa::WriteDefinition).assigns(value)),count(definition.getARead()),count(definition.getAFirstRead())

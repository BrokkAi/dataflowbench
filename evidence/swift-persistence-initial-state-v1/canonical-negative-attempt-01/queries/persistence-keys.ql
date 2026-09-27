/** @name Native AST literal keys on resolved persistence calls
 * @kind table
 * @id dfb/swift-persistence-keys
 */
import PersistenceIdentity
from MethodCallExpr call, Method target, Argument key, StringLiteralExpr literal
where selectedPersistenceCall(call, target) and key = call.getArgumentWithLabel("forKey") and
 literal = key.getExpr()
select call.getLocation().getStartLine(), target.getModule().getName(), target.getName(),
 key.getLabel(), literal.getValue(), literal.getLocation().getStartLine(), literal.getLocation().getStartColumn()

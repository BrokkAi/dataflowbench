/** @name V3 calibration endpoints
 * @kind table
 * @id dfb/swift-v3-calibration-roles
 */
import SwiftEndpoints
from DataFlow::Node n, string role
where benchmarkSource(n) and role="source" or benchmarkSink(n) and role="sink"
select n.getLocation().getFile().getBaseName(),n.getLocation().getStartLine(),n.getLocation().getStartColumn(),role

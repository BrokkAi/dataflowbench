func dfb_source() -> Int { 19 } // DFB-SOURCE: result-error-input
struct FlowError: Error { let value: Int }
func produce() -> Result<Int, FlowError> {
 return .failure(FlowError(value: dfb_source())) // DFB-WITNESS: result-error-raise
}
func relay() -> Result<Int, FlowError> {
 switch produce() {
 case .failure(let error):
  return .failure(error) // DFB-WITNESS: result-error-relay
 case .success(let value):
  return .success(value)
 }
}
func dfb_sink(_ value: Int) { precondition(value == 19) } // DFB-SINK: result-error-sink
func probe() {
 let clean = 0
 switch relay() {
 case .failure(let error):
  dfb_sink(error.value)
 case .success: break
 }
}
probe()

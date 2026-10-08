struct FlowError: Error {
    let value: Int
}

func dfb_source() -> Int { 7 }

func produce() -> Result<Int, FlowError> {
    let input = dfb_source() // DFB-SOURCE: result-error-input
    return .failure(FlowError(value: input)) // DFB-WITNESS: result-error-raise
}

func relay() -> Result<Int, FlowError> {
    switch produce() {
    case .failure(let error):
        return .failure(error) // DFB-WITNESS: result-error-relay
    case .success(let value):
        return .success(value)
    }
}

func dfb_sink(_ value: Int) {}

func probe() {
    switch relay() {
    case .failure(let error):
        let payload = error.value // DFB-WITNESS: result-error-payload
        dfb_sink(payload) // DFB-SINK: result-error-sink
    case .success:
        break
    }
}

probe()

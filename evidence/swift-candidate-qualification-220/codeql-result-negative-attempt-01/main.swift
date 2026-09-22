struct FlowError: Error {
    let value: Int
}

func dfb_source() -> Int { 7 }

func produce() -> Result<Int, FlowError> {
    let input = dfb_source() // DFB-SOURCE: result-error-negative-input
    return .failure(FlowError(value: input)) // DFB-WITNESS: result-error-negative-raise
}

func relay() -> Result<Int, FlowError> {
    switch produce() {
    case .failure(let error):
        return .failure(error) // DFB-WITNESS: result-error-negative-relay
    case .success(let value):
        return .success(value)
    }
}

func dfb_sink(_ value: Int) {}

func probe() {
    let clean = 0
    switch relay() {
    case .failure(let error):
        let payload = error.value // DFB-WITNESS: result-error-negative-payload
        dfb_sink(clean) // DFB-SINK: result-error-negative-sink
        _ = payload
    case .success:
        break
    }
}

probe()

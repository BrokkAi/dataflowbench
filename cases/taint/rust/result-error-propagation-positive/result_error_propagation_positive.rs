fn dfb_source() -> i32 { // DFB-SOURCE: result-error-input
    1
}

struct FlowError {
    value: i32,
}

fn produce() -> Result<i32, FlowError> {
    Err(FlowError { value: dfb_source() }) // DFB-WITNESS: result-error-raise
}

fn relay() -> Result<i32, FlowError> {
    let value = produce()?; // DFB-WITNESS: result-error-question-mark
    Ok(value)
}

fn dfb_sink(value: i32) {} // DFB-SINK: result-error-sink

fn run() {
    match relay() {
        Ok(_) => {}
        Err(error) => dfb_sink(error.value),
    }
}

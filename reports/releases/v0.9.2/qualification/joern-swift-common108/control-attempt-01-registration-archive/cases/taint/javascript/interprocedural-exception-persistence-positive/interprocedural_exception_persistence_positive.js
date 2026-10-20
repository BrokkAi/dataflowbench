function dfb_source() { // DFB-SOURCE: exception-persistence-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: exception-persistence-sink

class FlowError extends Error {}

class FlowBox {
  constructor(value) {
    this.value = value;
  }
}

function store_and_throw(box, value) {
  box.value = value; // DFB-WITNESS: exception-persistence-store
  throw new FlowError("exceptional exit"); // DFB-WITNESS: exception-persistence-throw
}

function recover(box, value) {
  try {
    store_and_throw(box, value);
    return "unreachable";
  } catch (error) {
    if (!(error instanceof FlowError)) throw error;
    return box.value; // DFB-WITNESS: exception-persistence-recovery
  }
}

function run() {
  dfb_sink(recover(new FlowBox("seed"), dfb_source()));
}

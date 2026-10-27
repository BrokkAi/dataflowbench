function dfb_source(): string { // DFB-SOURCE: exception-persistence-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: exception-persistence-sink

class FlowError extends Error {}

class FlowBox {
  value: string;

  constructor(value: string) {
    this.value = value;
  }
}

function store_and_throw(box: FlowBox, value: string): void {
  box.value = value; // DFB-WITNESS: exception-persistence-store
  throw new FlowError("exceptional exit"); // DFB-WITNESS: exception-persistence-throw
}

function recover(box: FlowBox, value: string): string {
  try {
    store_and_throw(box, value);
    return "unreachable";
  } catch (error) {
    if (!(error instanceof FlowError)) throw error;
    return box.value; // DFB-WITNESS: exception-persistence-recovery
  }
}

function run(): void {
  dfb_sink(recover(new FlowBox("seed"), dfb_source()));
}

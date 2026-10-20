function dfb_source(): string { // DFB-SOURCE: exception-catch-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: exception-catch-sink

interface FlowError extends Error {
  value: string;
}

function run(): void {
  try {
    const flow: FlowError = new Error("flow") as FlowError;
    flow.value = dfb_source();
    throw flow; // DFB-WITNESS: exception-catch-throw
  } catch (caught) {
    dfb_sink((caught as FlowError).value);
  }
}

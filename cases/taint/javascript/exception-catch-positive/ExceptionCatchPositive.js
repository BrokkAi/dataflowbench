function dfb_source() { // DFB-SOURCE: exception-catch-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: exception-catch-sink

function run() {
  try {
    const flow = new Error("flow");
    flow.value = dfb_source();
    throw flow; // DFB-WITNESS: exception-catch-throw
  } catch (caught) {
    dfb_sink(caught.value);
  }
}

function dfb_source() { // DFB-SOURCE: closure-capture-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: closure-capture-sink

function makeHandler() {
  const captured = dfb_source(); // DFB-WITNESS: closure-capture-store
  return () => {
    dfb_sink(captured);
  };
}

function run() {
  const handler = makeHandler();
  handler();
}

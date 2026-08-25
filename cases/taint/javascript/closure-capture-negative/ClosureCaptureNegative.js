function dfb_source() { // DFB-SOURCE: closure-capture-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: closure-capture-sink

function makeHandler() {
  const tainted = dfb_source(); // DFB-WITNESS: closure-capture-store
  const captured = "clean";
  return () => {
    dfb_sink(captured);
  };
}

function run() {
  const handler = makeHandler();
  handler();
}

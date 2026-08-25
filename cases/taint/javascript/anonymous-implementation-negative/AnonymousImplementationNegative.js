function dfb_source() { // DFB-SOURCE: anonymous-implementation-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: anonymous-implementation-sink

function run() {
  const leakHandler = function (value) { // DFB-WITNESS: anonymous-implementation-handler
    dfb_sink(value);
  };
  const dropHandler = function (value) {
    dfb_sink("clean");
  };
  dropHandler(dfb_source());
}

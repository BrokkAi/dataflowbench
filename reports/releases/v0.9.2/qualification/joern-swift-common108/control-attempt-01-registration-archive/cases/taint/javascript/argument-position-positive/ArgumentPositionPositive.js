function dfb_source() { // DFB-SOURCE: argument-position-input
  return "tainted";
}

function chooseFirst(first, second) { // DFB-WITNESS: argument-position-first
  return first;
}

function dfb_sink(value) {} // DFB-SINK: argument-position-sink

function run() {
  const result = chooseFirst(dfb_source(), "clean");
  dfb_sink(result);
}

function dfb_source() { // DFB-SOURCE: argument-position-negative-input
  return "tainted";
}

function chooseFirst(first, second) { // DFB-WITNESS: argument-position-negative-first
  return first;
}

function dfb_sink(value) {} // DFB-SINK: argument-position-negative-sink

function run() {
  const result = chooseFirst("clean", dfb_source());
  dfb_sink(result);
}

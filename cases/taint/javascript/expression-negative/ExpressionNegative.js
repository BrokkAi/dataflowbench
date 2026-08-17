function dfb_source() { // DFB-SOURCE: expression-negative-input
  return 4;
}

function dfb_sink(value) {} // DFB-SINK: expression-negative-sink

function run() {
  const value = dfb_source();
  const computed = (value * 3) + 7; // DFB-WITNESS: expression-negative-computed
  dfb_sink(7);
}

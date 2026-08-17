function dfb_source() { // DFB-SOURCE: expression-input
  return 4;
}

function dfb_sink(value) {} // DFB-SINK: expression-sink

function run() {
  const value = dfb_source();
  const computed = (value * 3) + 7; // DFB-WITNESS: expression-computed
  dfb_sink(computed);
}

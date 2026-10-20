function dfb_source() { // DFB-SOURCE: recursive-carry-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: recursive-carry-sink

function carry(value, depth) {
  if (depth === 0) {
    return "clean"; // DFB-WITNESS: recursive-carry-base
  }
  return carry(value, depth - 1);
}

function run() {
  dfb_sink(carry(dfb_source(), 5));
}

function dfb_source() { // DFB-SOURCE: direct-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: direct-sink

function run() {
  dfb_sink(dfb_source());
}


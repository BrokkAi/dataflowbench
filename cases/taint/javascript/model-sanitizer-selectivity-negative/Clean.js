function scrub(value) {
  return value;
}

function sanitize(value) {
  return value;
}

function dfb_source() { // DFB-SOURCE: model-sanitizer-selectivity-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-sanitizer-selectivity-sink

function run() {
  dfb_sink(scrub(dfb_source()));
}

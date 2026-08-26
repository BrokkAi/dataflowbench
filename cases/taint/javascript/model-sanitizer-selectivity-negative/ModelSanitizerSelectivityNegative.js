function dfb_source() { // DFB-SOURCE: model-sanitizer-selectivity-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-sanitizer-selectivity-sink

const Clean = {
  scrub: function scrub(value) {
    return value;
  },
  sanitize: function sanitize(value) {
    return value;
  }
};

function run() {
  dfb_sink(Clean.scrub(dfb_source()));
}

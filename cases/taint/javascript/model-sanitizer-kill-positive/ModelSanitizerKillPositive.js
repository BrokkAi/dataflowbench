function dfb_source() { // DFB-SOURCE: model-sanitizer-kill-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-sanitizer-kill-sink

const Clean = {
  scrub: function scrub(value) {
    return value;
  }
};

function run() {
  dfb_sink(dfb_source());
}

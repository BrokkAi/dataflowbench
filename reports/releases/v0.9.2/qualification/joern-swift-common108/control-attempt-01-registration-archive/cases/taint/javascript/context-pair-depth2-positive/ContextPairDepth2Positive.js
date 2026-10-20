function dfb_source() { // DFB-SOURCE: context-pair-depth2-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: context-pair-depth2-sink

function helper(value) { // DFB-WITNESS: context-pair-depth2-helper
  return value;
}

function wrapper(value) {
  return helper(value);
}

function outerTainted() {
  return wrapper(dfb_source());
}

function outerClean() {
  return wrapper("clean");
}

function run() {
  const tainted = outerTainted();
  const clean = outerClean();
  dfb_sink(tainted);
}

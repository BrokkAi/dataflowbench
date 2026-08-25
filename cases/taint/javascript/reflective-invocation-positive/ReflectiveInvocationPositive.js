function dfb_source() { // DFB-SOURCE: reflective-invocation-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: reflective-invocation-sink

const handlers = {
  leak(value) { // DFB-WITNESS: reflective-invocation-target
    dfb_sink(value);
  },
  drop(value) {
    dfb_sink("clean");
  }
};

function run() {
  const name = "leak";
  handlers[name](dfb_source());
}

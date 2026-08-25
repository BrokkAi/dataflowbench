function dfb_source() { // DFB-SOURCE: function-field-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: function-field-sink

function invoke(target, value) {
  target.fn(value);
}

function run() {
  const holder = { fn: null };
  const otherHolder = { fn: null };
  holder.fn = (value) => { // DFB-WITNESS: function-field-store
    dfb_sink(value);
  };
  otherHolder.fn = (value) => {
    dfb_sink("clean");
  };
  invoke(holder, dfb_source());
}

function dfb_source() { // DFB-SOURCE: dispatch-table-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: dispatch-table-sink

const table = {
  leak: (value) => { // DFB-WITNESS: dispatch-table-entry
    dfb_sink(value);
  },
  drop: (value) => {
    dfb_sink("clean");
  }
};

function run() {
  const key = "drop";
  const selected = table[key];
  selected(dfb_source());
}

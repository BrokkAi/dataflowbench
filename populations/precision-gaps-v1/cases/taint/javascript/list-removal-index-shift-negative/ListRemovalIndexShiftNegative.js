function dfb_source() { // DFB-SOURCE: list-removal-index-shift-input
  return process.env.DFB_INPUT ?? "";
}

function dfb_sink(value) { // DFB-SINK: list-removal-index-shift-sink
  console.log(value);
}

const values = [];
values.push("safe");
values.push(dfb_source());
values.push("more-safe");
values.shift(); // DFB-WITNESS: list-removal-index-shift-remove-first
dfb_sink(values[1]);

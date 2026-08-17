function dfb_source() { // DFB-SOURCE: loop-carried-input
  return 1;
}

function dfb_sink(value) {} // DFB-SINK: loop-carried-sink

function run() {
  let value = dfb_source();
  for (let iteration = 0; iteration < 3; iteration++) {
    value = 0; // DFB-WITNESS: loop-carried-value
  }
  dfb_sink(value);
}

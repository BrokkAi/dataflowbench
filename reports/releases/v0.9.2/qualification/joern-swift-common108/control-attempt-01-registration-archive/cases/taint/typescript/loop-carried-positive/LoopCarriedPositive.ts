function dfb_source(): number { // DFB-SOURCE: loop-carried-input
  return 1;
}

function dfb_sink(value: number): void {} // DFB-SINK: loop-carried-sink

function run(): void {
  let value: number = dfb_source();
  for (let iteration: number = 0; iteration < 3; iteration++) {
    value = value + iteration; // DFB-WITNESS: loop-carried-value
  }
  dfb_sink(value);
}

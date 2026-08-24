function dfb_source(): number { // DFB-SOURCE: expression-negative-input
  return 4;
}

function dfb_sink(value: number): void {} // DFB-SINK: expression-negative-sink

function run(): void {
  const value: number = dfb_source();
  const computed: number = (value * 3) + 7; // DFB-WITNESS: expression-negative-computed
  dfb_sink(7);
}

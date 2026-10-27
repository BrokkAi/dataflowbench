function dfb_source(): number { // DFB-SOURCE: expression-input
  return 4;
}

function dfb_sink(value: number): void {} // DFB-SINK: expression-sink

function run(): void {
  const value: number = dfb_source();
  const computed: number = (value * 3) + 7; // DFB-WITNESS: expression-computed
  dfb_sink(computed);
}

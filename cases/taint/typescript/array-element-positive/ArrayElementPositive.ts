function dfb_source(): string { // DFB-SOURCE: array-element-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: array-element-sink

function run(): void {
  const values: string[] = ["clean", "clean"];
  values[0] = dfb_source(); // DFB-WITNESS: array-element-store
  values[1] = "clean";
  dfb_sink(values[0]);
}

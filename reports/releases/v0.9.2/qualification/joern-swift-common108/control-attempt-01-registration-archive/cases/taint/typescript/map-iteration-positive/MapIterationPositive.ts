function dfb_source(): string { // DFB-SOURCE: map-iteration-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: map-iteration-sink

function run(): void {
  const carrier: Record<string, string> = { payload: "clean" };
  const other: Record<string, string> = { payload: "clean" };
  carrier.payload = dfb_source(); // DFB-WITNESS: map-iteration-store
  for (const [key, value] of Object.entries(carrier)) {
    dfb_sink(value);
  }
}

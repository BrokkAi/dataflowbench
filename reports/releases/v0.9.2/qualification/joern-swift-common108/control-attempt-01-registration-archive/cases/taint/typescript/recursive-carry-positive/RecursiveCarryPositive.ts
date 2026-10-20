function dfb_source(): string { // DFB-SOURCE: recursive-carry-input
  return "tainted";
}

function dfb_sink(value: string): void {} // DFB-SINK: recursive-carry-sink

function carry(value: string, depth: number): string {
  if (depth === 0) {
    return value; // DFB-WITNESS: recursive-carry-base
  }
  return carry(value, depth - 1);
}

function run(): void {
  dfb_sink(carry(dfb_source(), 5));
}

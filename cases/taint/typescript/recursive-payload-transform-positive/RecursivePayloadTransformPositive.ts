function dfb_source(): number { // DFB-SOURCE: recursive-payload-transform-input
  return 7;
}

function dfb_sink(value: number): void {} // DFB-SINK: recursive-payload-transform-sink

function walk(value: number, depth: number): number {
  if (depth === 0) {
    return value; // DFB-WITNESS: recursive-payload-transform-base
  }
  const next: number = value + 1;
  const recursiveResult: number = walk(next, depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
  return recursiveResult + 1; // DFB-WITNESS: recursive-payload-transform-compose
}

function run(): void {
  dfb_sink(walk(dfb_source(), 3));
}

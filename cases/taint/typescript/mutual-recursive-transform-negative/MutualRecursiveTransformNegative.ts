function dfb_source(): number { // DFB-SOURCE: mutual-recursive-transform-input
  return 7;
}

function dfb_sink(value: number): void {} // DFB-SINK: mutual-recursive-transform-sink

function walkA(value: number, depth: number): number {
  if (depth === 0) {
    value = 0; // DFB-KILL: mutual-recursive-transform-a-base-clean
    return value; // DFB-WITNESS: mutual-recursive-transform-a-base
  }
  const next: number = value + 1;
  const recursiveResult: number = walkB(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-a-transfer
  return recursiveResult + 1; // DFB-WITNESS: mutual-recursive-transform-a-compose
}

function walkB(value: number, depth: number): number {
  if (depth === 0) {
    value = 0; // DFB-KILL: mutual-recursive-transform-b-base-clean
    return value; // DFB-WITNESS: mutual-recursive-transform-b-base
  }
  const next: number = value + 1;
  const recursiveResult: number = walkA(next, depth - 1); // DFB-WITNESS: mutual-recursive-transform-b-transfer
  return recursiveResult + 1; // DFB-WITNESS: mutual-recursive-transform-b-compose
}

function run(): void {
  dfb_sink(walkA(dfb_source(), 3));
}

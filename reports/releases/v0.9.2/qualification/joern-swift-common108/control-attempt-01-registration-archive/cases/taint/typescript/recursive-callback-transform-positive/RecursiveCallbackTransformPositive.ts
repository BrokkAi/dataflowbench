type Step = (value: number, depth: number) => number;

function dfb_source(): number { // DFB-SOURCE: recursive-callback-transform-input
  return 7;
}

function dfb_sink(value: number): void {} // DFB-SINK: recursive-callback-transform-sink

function walk(value: number, depth: number, step: Step): number {
  if (depth === 0) {
    return value; // DFB-WITNESS: recursive-callback-transform-base
  }
  return step(value, depth - 1); // DFB-WITNESS: recursive-callback-transform-indirect-transfer
}

function step(value: number, depth: number): number {
  const next: number = value + 1; // DFB-WITNESS: recursive-callback-transform-step
  const recursiveResult: number = walk(next, depth, step); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
  return recursiveResult + 1; // DFB-WITNESS: recursive-callback-transform-compose
}

function run(): void {
  dfb_sink(walk(dfb_source(), 3, step));
}

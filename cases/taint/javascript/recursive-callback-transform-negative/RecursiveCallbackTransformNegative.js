function dfb_source() { // DFB-SOURCE: recursive-callback-transform-input
  return 7;
}

function dfb_sink(value) { } // DFB-SINK: recursive-callback-transform-sink

function walk(value, depth, step) {
  if (depth === 0) {
    value = 0; // DFB-KILL: recursive-callback-transform-base-overwrite
    return value; // DFB-WITNESS: recursive-callback-transform-base
  }
  return step(value, depth - 1); // DFB-WITNESS: recursive-callback-transform-transfer
}

function step(value, depth) {
  const nextValue = value + 1; // DFB-WITNESS: recursive-callback-transform-step
  const recursiveResult = walk(nextValue, depth, step); // DFB-WITNESS: recursive-callback-transform-recursive-transfer
  return recursiveResult + 1; // DFB-WITNESS: recursive-callback-transform-compose
}

function run() {
  dfb_sink(walk(dfb_source(), 3, step));
}

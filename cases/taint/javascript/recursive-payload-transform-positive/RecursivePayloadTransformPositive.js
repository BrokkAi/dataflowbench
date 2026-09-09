function dfb_source() { // DFB-SOURCE: recursive-payload-transform-input
  return 7;
}

function dfb_sink(value) { } // DFB-SINK: recursive-payload-transform-sink

function walk(value, depth) {
  if (depth === 0) {
    return value; // DFB-WITNESS: recursive-payload-transform-base
  }
  const nextValue = value + 1;
  const recursiveResult = walk(nextValue, depth - 1); // DFB-WITNESS: recursive-payload-transform-transfer
  return recursiveResult + 1; // DFB-WITNESS: recursive-payload-transform-compose
}

function run() {
  dfb_sink(walk(dfb_source(), 3));
}

function dfb_source() { // DFB-SOURCE: mutual-recursive-transform-input
  return 7;
}

function dfb_sink(value) { } // DFB-SINK: mutual-recursive-transform-sink

function walkA(value, depth) {
  if (depth === 0) {
    return value; // DFB-WITNESS: mutual-recursive-transform-a-base
  }
  const nextValue = value + 1;
  const recursiveResult = walkB(nextValue, depth - 1); // DFB-WITNESS: mutual-recursive-transform-a-transfer
  return recursiveResult + 1; // DFB-WITNESS: mutual-recursive-transform-a-compose
}

function walkB(value, depth) {
  if (depth === 0) {
    return value; // DFB-WITNESS: mutual-recursive-transform-b-base
  }
  const nextValue = value + 1;
  const recursiveResult = walkA(nextValue, depth - 1); // DFB-WITNESS: mutual-recursive-transform-b-transfer
  return recursiveResult + 1; // DFB-WITNESS: mutual-recursive-transform-b-compose
}

function run() {
  dfb_sink(walkA(dfb_source(), 3));
}

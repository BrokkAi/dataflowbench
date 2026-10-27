function dfb_source() { // DFB-SOURCE: recursive-heap-unwind-input
  return 7;
}

function dfb_sink(value) { } // DFB-SINK: recursive-heap-unwind-sink

function walk(box, value, depth) {
  if (depth === 0) {
    box.value = value; // DFB-WITNESS: recursive-heap-unwind-base
    return;
  }
  walk(box, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
  box.value = box.value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
}

function run() {
  const box = { value: 0 };
  walk(box, dfb_source(), 3);
  dfb_sink(box.value);
}

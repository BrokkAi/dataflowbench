interface FlowBox {
  value: number;
}

function dfb_source(): number { // DFB-SOURCE: recursive-heap-unwind-input
  return 7;
}

function dfb_sink(value: number): void {} // DFB-SINK: recursive-heap-unwind-sink

function walk(box: FlowBox, value: number, depth: number): void {
  if (depth === 0) {
    box.value = value; // DFB-WITNESS: recursive-heap-unwind-base
    box.value = 0; // DFB-KILL: recursive-heap-unwind-base-clean
    return;
  }
  walk(box, value, depth - 1); // DFB-WITNESS: recursive-heap-unwind-transfer
  box.value = box.value + 1; // DFB-WITNESS: recursive-heap-unwind-compose
}

function run(): void {
  const box: FlowBox = { value: 0 };
  walk(box, dfb_source(), 3);
  dfb_sink(box.value);
}

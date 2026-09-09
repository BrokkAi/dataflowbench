interface FlowBox {
  value: number;
}

class RecursiveSignal extends Error {}

function dfb_source(): number { // DFB-SOURCE: recursive-exception-persistence-input
  return 7;
}

function dfb_sink(value: number): void {} // DFB-SINK: recursive-exception-persistence-sink

function walk(box: FlowBox, value: number, depth: number): never {
  if (depth === 0) {
    box.value = value; // DFB-WITNESS: recursive-exception-persistence-base
    box.value = 0; // DFB-KILL: recursive-exception-persistence-base-clean
    throw new RecursiveSignal("recursive exceptional exit"); // DFB-WITNESS: recursive-exception-persistence-throw
  }
  return walk(box, value, depth - 1); // DFB-WITNESS: recursive-exception-persistence-transfer
}

function run(): void {
  const box: FlowBox = { value: 0 };
  try {
    walk(box, dfb_source(), 3);
  } catch (caught: unknown) {
    if (caught instanceof RecursiveSignal) { // DFB-WITNESS: recursive-exception-persistence-catch
      const result: number = box.value + 1; // DFB-WITNESS: recursive-exception-persistence-compose
      dfb_sink(result);
    }
  }
}

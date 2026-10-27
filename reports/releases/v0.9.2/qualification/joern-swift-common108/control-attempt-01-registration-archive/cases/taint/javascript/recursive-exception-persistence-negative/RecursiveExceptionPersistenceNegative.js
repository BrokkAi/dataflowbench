function dfb_source() { // DFB-SOURCE: recursive-exception-persistence-input
  return 7;
}

function dfb_sink(value) { } // DFB-SINK: recursive-exception-persistence-sink

class RecursiveSignal extends Error {}

function walk(box, value, depth) {
  if (depth === 0) {
    box.value = value; // DFB-WITNESS: recursive-exception-persistence-base
    box.value = 0; // DFB-KILL: recursive-exception-persistence-base-overwrite
    throw new RecursiveSignal("recursive exceptional exit"); // DFB-WITNESS: recursive-exception-persistence-throw
  }
  walk(box, value, depth - 1); // DFB-WITNESS: recursive-exception-persistence-transfer
}

function run() {
  const box = { value: 0 };
  try {
    walk(box, dfb_source(), 3);
  } catch (error) {
    if (!(error instanceof RecursiveSignal)) throw error; // DFB-WITNESS: recursive-exception-persistence-catch
    const result = box.value + 1; // DFB-WITNESS: recursive-exception-persistence-compose
    dfb_sink(result);
  }
}

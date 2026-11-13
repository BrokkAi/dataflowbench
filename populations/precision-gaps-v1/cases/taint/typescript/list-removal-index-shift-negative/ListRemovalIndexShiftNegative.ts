declare const process: { env: { DFB_INPUT?: string } };

function dfb_source(): string { // DFB-SOURCE: list-removal-index-shift-input
  return process.env.DFB_INPUT ?? "";
}

function dfb_sink(value: string): void { // DFB-SINK: list-removal-index-shift-sink
  console.log(value);
}

const values: string[] = [];
values.push("safe");
values.push(dfb_source());
values.push("more-safe");
values.shift(); // DFB-WITNESS: list-removal-index-shift-remove-first
dfb_sink(values[1]);

function dfb_source() { // DFB-SOURCE: folded-local-constant-source
  return "tainted";
}

function dfb_sink(value) { // DFB-SINK: folded-local-constant-sink
  console.log(value);
}

function run() {
  const factor = 7;
  const num = 100;
  const limit = 200;
  let value;
  if ((factor * 42) - num > limit) {
    value = "safe";
  } else {
    value = dfb_source(); // DFB-WITNESS: folded-local-constant-source-selected
  }
  dfb_sink(value);
}

run();

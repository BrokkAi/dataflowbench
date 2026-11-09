function dfb_source() { // DFB-SOURCE: folded-local-constant-source
  return "tainted";
}

function dfb_sink(value) { // DFB-SINK: folded-local-constant-sink
  console.log(value);
}

function run() {
  const factor = 7;
  const num = 86;
  const limit = 200;
  let value;
  if ((factor * 42) - num > limit) {
    value = "safe";
  } else {
    value = dfb_source();
  }
  dfb_sink(value);
}

run();

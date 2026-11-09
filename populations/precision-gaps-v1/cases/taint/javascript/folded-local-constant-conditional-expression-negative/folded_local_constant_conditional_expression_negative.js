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
  const value = ((factor * 42) - num > limit)
    ? "safe"
    : /* */ dfb_source();
  dfb_sink(value);
}

run();

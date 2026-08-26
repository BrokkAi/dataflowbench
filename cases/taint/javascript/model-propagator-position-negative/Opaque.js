function dfb_source() { // DFB-SOURCE: model-propagator-position-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-propagator-position-sink

const _impl = {
  identity: function identity(first, second) {
    return second;
  }
};

const Opaque = {
  select: function select(first, second) {
    const target = "identity";
    return Reflect.get(_impl, target).apply(null, [first, second]);
  }
};

function run() {
  dfb_sink(Opaque.select(dfb_source(), "clean"));
}

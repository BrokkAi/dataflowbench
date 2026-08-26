function dfb_source() { // DFB-SOURCE: model-opaque-propagator-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-opaque-propagator-sink

const _impl = {
  identity: function identity(value) {
    return value;
  }
};

const Opaque = {
  carry: function carry(value) {
    const target = "identity";
    return Reflect.get(_impl, target).apply(null, [value]);
  },
  block: function block(value) {
    const target = "identity";
    return Reflect.get(_impl, target).apply(null, [value]);
  }
};

function run() {
  dfb_sink(Opaque.block(dfb_source()));
}

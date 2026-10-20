function dfb_sink(value) {} // DFB-SINK: model-entrypoint-selectivity-sink

const Handler = {
  onDeclared: function onDeclared(input) { // DFB-SOURCE: model-entrypoint-selectivity-input
    dfb_sink(input);
  },
  onUndeclared: function onUndeclared(input) {
    dfb_sink("clean");
  }
};

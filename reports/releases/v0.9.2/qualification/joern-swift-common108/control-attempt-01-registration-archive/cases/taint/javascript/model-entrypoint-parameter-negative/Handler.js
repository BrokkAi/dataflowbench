function dfb_sink(value) {} // DFB-SINK: model-entrypoint-parameter-sink

const Handler = {
  onRequest: function onRequest(input) { // DFB-SOURCE: model-entrypoint-parameter-input
    dfb_sink("clean");
  },
  onIgnored: function onIgnored(input) {
    dfb_sink(input);
  }
};

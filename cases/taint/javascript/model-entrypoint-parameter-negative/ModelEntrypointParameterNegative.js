function dfb_sink(value) {} // DFB-SINK: model-entrypoint-parameter-sink

const Handler = {
  onIgnored: function onIgnored(input) { // DFB-SOURCE: model-entrypoint-parameter-input
    dfb_sink(input);
  }
};

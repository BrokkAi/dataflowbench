const Config = {
  fetchRemote: function fetchRemote() {
    return "r";
  },
  fetchLocal: function fetchLocal() { // DFB-SOURCE: model-declared-source-input
    return "l";
  }
};

function dfb_sink(value) {} // DFB-SINK: model-declared-source-sink

function run() {
  dfb_sink(Config.fetchLocal());
}

class Store {
  put(key, value) {}

  get(key) {
    return "";
  }
}

const alpha = new Store();
const beta = new Store();

function dfb_source() { // DFB-SOURCE: model-store-separation-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-store-separation-sink

function writeSide() {
  alpha.put("k", dfb_source());
}

function readSide() {
  dfb_sink(alpha.get("k"));
}

function dfb_source() { // DFB-SOURCE: model-store-roundtrip-input
  return "tainted";
}

function dfb_sink(value) {} // DFB-SINK: model-store-roundtrip-sink

class Store {
  static put(key, value) {}

  static get(key) {}
}

function writeSide() {
  Store.put("k", dfb_source());
}

function readSide() {
  dfb_sink(Store.get("k"));
}

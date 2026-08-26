package dataflowbench.taint;

final class Store {
    static void put(String key, String value) { }

    static String get(String key) {
        return "";
    }
}

final class ModelStoreRoundtripNegative {
    static String dfb_source() {  // DFB-SOURCE: model-store-roundtrip-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-store-roundtrip-sink

    static void writeSide() {
        Store.put("a", dfb_source());
    }

    static void readSide() {
        dfb_sink(Store.get("b"));
    }
}

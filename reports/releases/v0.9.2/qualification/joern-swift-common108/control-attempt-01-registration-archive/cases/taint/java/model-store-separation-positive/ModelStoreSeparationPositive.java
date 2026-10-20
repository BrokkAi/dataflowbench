package dataflowbench.taint;

final class Store {
    void put(String key, String value) { }

    String get(String key) {
        return "";
    }
}

final class ModelStoreSeparationPositive {
    static final Store alpha = new Store();

    static final Store beta = new Store();

    static String dfb_source() {  // DFB-SOURCE: model-store-separation-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-store-separation-sink

    static void writeSide() {
        alpha.put("k", dfb_source());
    }

    static void readSide() {
        dfb_sink(alpha.get("k"));
    }
}

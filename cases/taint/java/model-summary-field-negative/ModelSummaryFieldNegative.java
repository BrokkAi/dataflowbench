package dataflowbench.taint;

final class Box {
    String payload = "";
    String spare = "";
}

final class Bridge {
    static void deposit(String value, Box box) { }
}

final class ModelSummaryFieldNegative {
    static String dfb_source() {  // DFB-SOURCE: model-summary-field-input
        return "t";
    }

    static void dfb_sink(String value) { }  // DFB-SINK: model-summary-field-sink

    static void run() {
        Box box = new Box();
        Bridge.deposit(dfb_source(), box);
        dfb_sink(box.spare);
    }
}

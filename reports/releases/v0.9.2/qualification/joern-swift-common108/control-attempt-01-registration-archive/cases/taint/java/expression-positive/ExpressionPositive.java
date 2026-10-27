package dataflowbench.taint;

final class ExpressionPositive {
    static int dfb_source() { // DFB-SOURCE: expression-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: expression-sink

    static void run() {
        int value = dfb_source();
        int computed = (value * 3) + 7; // DFB-WITNESS: expression-computed
        dfb_sink(computed);
    }
}

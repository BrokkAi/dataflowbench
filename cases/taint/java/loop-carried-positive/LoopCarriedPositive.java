package dataflowbench.taint;

final class LoopCarriedPositive {
    static int dfb_source() { // DFB-SOURCE: loop-carried-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: loop-carried-sink

    static void run() {
        int value = dfb_source();
        for (int iteration = 0; iteration < 3; iteration++) {
            value = value + iteration; // DFB-WITNESS: loop-carried-value
        }
        dfb_sink(value);
    }
}

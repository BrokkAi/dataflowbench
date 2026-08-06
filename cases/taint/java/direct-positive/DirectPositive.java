package dataflowbench.taint;

final class DirectPositive {
    static int directUntrustedInput() { // DFB-SOURCE: direct-input
        return 1;
    }

    static void recordDirect(int value) { } // DFB-SINK: direct-sink

    static void run() {
        recordDirect(directUntrustedInput());
    }
}

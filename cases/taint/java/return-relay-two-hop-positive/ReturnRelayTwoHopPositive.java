package dataflowbench.taint;

final class ReturnRelayTwoHopPositive {
    static int dfb_source() { // DFB-SOURCE: return-two-hop-input
        return 1;
    }

    static int firstRelay(int value) { // DFB-WITNESS: return-two-hop-first
        return value;
    }

    static int secondRelay(int value) { // DFB-WITNESS: return-two-hop-second
        return firstRelay(value);
    }

    static void dfb_sink(int value) { } // DFB-SINK: return-two-hop-sink

    static void run() {
        int result = secondRelay(dfb_source());
        dfb_sink(result);
    }
}

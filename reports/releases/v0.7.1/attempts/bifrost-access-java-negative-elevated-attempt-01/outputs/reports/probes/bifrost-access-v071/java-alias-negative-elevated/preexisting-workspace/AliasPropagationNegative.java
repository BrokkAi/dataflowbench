package dataflowbench.taint;

final class AliasPropagationNegative {
    static final class Holder {
        int value;
    }

    static int dfb_source() { // DFB-SOURCE: alias-propagation-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: alias-propagation-sink

    static void run() {
        Holder original = new Holder();
        Holder alias = original; // DFB-WITNESS: alias-propagation-alias
        Holder distinct = new Holder();
        original.value = dfb_source(); // DFB-WITNESS: alias-propagation-store
        dfb_sink(distinct.value);
    }
}

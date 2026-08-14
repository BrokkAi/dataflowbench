package dataflowbench.taint;

final class ObjectSeparationPositive {
    static final class Holder {
        int value;
    }

    static int dfb_source() { // DFB-SOURCE: object-separation-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: object-separation-sink

    static void run() {
        Holder tainted = new Holder();
        Holder clean = new Holder();
        tainted.value = dfb_source(); // DFB-WITNESS: object-separation-store
        clean.value = 0;
        dfb_sink(tainted.value);
    }
}

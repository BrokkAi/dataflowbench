package dataflowbench.taint;

final class NestedAccessPathNegative {
    static final class Leaf {
        int value;
        int other;
    }

    static final class Middle {
        final Leaf c = new Leaf();
    }

    static final class Outer {
        final Middle b = new Middle();
    }

    static int dfb_source() { // DFB-SOURCE: nested-access-path-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: nested-access-path-sink

    static void run() {
        Outer a = new Outer();
        a.b.c.value = dfb_source(); // DFB-WITNESS: nested-access-path-store
        a.b.c.other = 0;
        dfb_sink(a.b.c.other);
    }
}

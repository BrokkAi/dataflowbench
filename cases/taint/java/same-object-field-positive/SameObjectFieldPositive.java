package dataflowbench.taint;

final class SameObjectFieldPositive {
    static final class Holder {
        int tainted;
        int clean;
    }

    static int dfb_source() { // DFB-SOURCE: same-object-field-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: same-object-field-sink

    static void run() {
        Holder holder = new Holder();
        holder.tainted = dfb_source(); // DFB-WITNESS: same-object-field-store
        holder.clean = 0;
        dfb_sink(holder.tainted);
    }
}

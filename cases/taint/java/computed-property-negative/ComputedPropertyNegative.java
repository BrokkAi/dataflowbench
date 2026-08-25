package dataflowbench.taint;

import java.lang.reflect.Field;

final class ComputedPropertyNegative {
    static final class Holder {
        int tainted;
        int clean;
    }

    static int dfb_source() { // DFB-SOURCE: computed-property-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: computed-property-sink

    static void run() throws Exception {
        Holder holder = new Holder();
        String writeKey = "tainted";
        String readKey = "clean";
        Field written = Holder.class.getDeclaredField(writeKey); // DFB-WITNESS: computed-property-member
        written.setInt(holder, dfb_source()); // DFB-WITNESS: computed-property-store
        Field read = Holder.class.getDeclaredField(readKey);
        dfb_sink(read.getInt(holder));
    }
}

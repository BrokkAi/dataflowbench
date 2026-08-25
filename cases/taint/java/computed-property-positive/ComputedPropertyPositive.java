package dataflowbench.taint;

import java.lang.reflect.Field;

final class ComputedPropertyPositive {
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
        String key = "tainted";
        Field member = Holder.class.getDeclaredField(key); // DFB-WITNESS: computed-property-member
        member.setInt(holder, dfb_source()); // DFB-WITNESS: computed-property-store
        dfb_sink(member.getInt(holder));
    }
}

package dataflowbench.taint;

final class ElementObjectPositive {
    static final class Item {
        int value;
    }

    static int dfb_source() { // DFB-SOURCE: element-object-input
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: element-object-sink

    static void run() {
        Item[] items = new Item[] {new Item(), new Item()};
        items[0].value = dfb_source(); // DFB-WITNESS: element-object-store
        items[1].value = 0;
        dfb_sink(items[0].value);
    }
}

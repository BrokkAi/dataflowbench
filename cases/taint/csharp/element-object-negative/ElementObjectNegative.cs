namespace DataFlowBench;

static class ElementObjectNegative
{
    sealed class Item
    {
        public string Value = "clean";
    }

    static string dfb_source() // DFB-SOURCE: element-object-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: element-object-sink

    static void Run()
    {
        Item[] items = new Item[] { new Item(), new Item() };
        items[0].Value = dfb_source(); // DFB-WITNESS: element-object-store
        dfb_sink(items[1].Value);
    }
}

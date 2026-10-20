namespace DataFlowBench;

static class LocalOverwritePositive
{
    static int dfb_source() // DFB-SOURCE: local-overwrite-input
    {
        return 1;
    }

    static void dfb_sink(int value) { } // DFB-SINK: local-overwrite-sink

    static void Run()
    {
        int value = dfb_source();
        value = value; // DFB-WITNESS: local-overwrite-preserved
        dfb_sink(value);
    }
}

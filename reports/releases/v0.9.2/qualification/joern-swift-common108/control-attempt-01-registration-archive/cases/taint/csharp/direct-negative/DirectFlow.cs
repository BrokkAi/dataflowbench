namespace DataFlowBench;

static class DirectFlow
{
    static string dfb_source() // DFB-SOURCE: direct-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: direct-sink

    static void Run()
    {
        dfb_source();
        dfb_sink("clean");
    }
}

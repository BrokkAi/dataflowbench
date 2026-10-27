namespace DataFlowBench;

static class AnonymousImplementationNegative
{
    delegate void Handler(string value);

    static string dfb_source() // DFB-SOURCE: anonymous-implementation-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: anonymous-implementation-sink

    static void Run()
    {
        Handler leakHandler = delegate (string value) // DFB-WITNESS: anonymous-implementation-handler
        {
            dfb_sink(value);
        };
        Handler dropHandler = delegate (string value)
        {
            dfb_sink("clean");
        };
        dropHandler(dfb_source());
    }
}

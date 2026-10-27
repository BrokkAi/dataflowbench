namespace DataFlowBench;

static class ContextPairDepth2Negative
{
    static string dfb_source() // DFB-SOURCE: context-pair-depth2-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: context-pair-depth2-sink

    static string Helper(string value) // DFB-WITNESS: context-pair-depth2-helper
    {
        return value;
    }

    static string Wrapper(string value)
    {
        return Helper(value);
    }

    static string OuterTainted()
    {
        return Wrapper(dfb_source());
    }

    static string OuterClean()
    {
        return Wrapper("clean");
    }

    static void Run()
    {
        string tainted = OuterTainted();
        string clean = OuterClean();
        dfb_sink(clean);
    }
}

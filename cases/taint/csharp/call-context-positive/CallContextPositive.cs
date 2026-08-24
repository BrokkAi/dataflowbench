namespace DataFlowBench;

static class CallContextPositive
{
    static int dfb_source() // DFB-SOURCE: call-context-input
    {
        return 1;
    }

    static int Relay(int value) // DFB-WITNESS: call-context-relay
    {
        return value;
    }

    static void dfb_sink(int value) { } // DFB-SINK: call-context-sink

    static void Run()
    {
        int tainted = Relay(dfb_source());
        int clean = Relay(0);
        dfb_sink(tainted);
    }
}

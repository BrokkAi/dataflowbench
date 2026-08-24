namespace DataFlowBench;

static class ReturnRelayOneHopPositive
{
    static int dfb_source() // DFB-SOURCE: return-one-hop-input
    {
        return 1;
    }

    static int Relay(int value) // DFB-WITNESS: return-one-hop-relay
    {
        return value;
    }

    static void dfb_sink(int value) { } // DFB-SINK: return-one-hop-sink

    static void Run()
    {
        int result = Relay(dfb_source());
        dfb_sink(result);
    }
}

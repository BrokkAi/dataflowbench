namespace DataFlowBench;

static class ReturnRelayTwoHopNegative
{
    static int dfb_source() // DFB-SOURCE: return-two-hop-negative-input
    {
        return 1;
    }

    static int FirstRelay(int value) // DFB-WITNESS: return-two-hop-negative-first
    {
        return value;
    }

    static int SecondRelay(int value) // DFB-WITNESS: return-two-hop-negative-second
    {
        return FirstRelay(value);
    }

    static void dfb_sink(int value) { } // DFB-SINK: return-two-hop-negative-sink

    static void Run()
    {
        int result = SecondRelay(dfb_source());
        dfb_sink(0);
    }
}

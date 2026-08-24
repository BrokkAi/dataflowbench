namespace DataFlowBench;

static class ReturnRelayTwoHopPositive
{
    static int dfb_source() // DFB-SOURCE: return-two-hop-input
    {
        return 1;
    }

    static int FirstRelay(int value) // DFB-WITNESS: return-two-hop-first
    {
        return value;
    }

    static int SecondRelay(int value) // DFB-WITNESS: return-two-hop-second
    {
        return FirstRelay(value);
    }

    static void dfb_sink(int value) { } // DFB-SINK: return-two-hop-sink

    static void Run()
    {
        int result = SecondRelay(dfb_source());
        dfb_sink(result);
    }
}

namespace DataFlowBench;

static class DeepRelayChainPositive
{
    static string dfb_source() // DFB-SOURCE: deep-relay-chain-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: deep-relay-chain-sink

    static void Relay6(string value) // DFB-WITNESS: deep-relay-chain-hop-six
    {
        dfb_sink(value);
    }

    static void Relay5(string value)
    {
        Relay6(value);
    }

    static void Relay4(string value)
    {
        Relay5(value);
    }

    static void Relay3(string value)
    {
        Relay4(value);
    }

    static void Relay2(string value)
    {
        Relay3(value);
    }

    static void Relay1(string value) // DFB-WITNESS: deep-relay-chain-hop-one
    {
        Relay2(value);
    }

    static void Run()
    {
        Relay1(dfb_source());
    }
}

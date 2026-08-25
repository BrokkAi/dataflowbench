using System;

namespace DataFlowBench;

static class ClosureCaptureNegative
{
    static string dfb_source() // DFB-SOURCE: closure-capture-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: closure-capture-sink

    static Action MakeHandler()
    {
        string tainted = dfb_source(); // DFB-WITNESS: closure-capture-store
        string captured = "clean";
        return () =>
        {
            dfb_sink(captured);
        };
    }

    static void Run()
    {
        Action handler = MakeHandler();
        handler();
    }
}

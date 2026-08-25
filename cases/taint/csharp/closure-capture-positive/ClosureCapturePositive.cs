using System;

namespace DataFlowBench;

static class ClosureCapturePositive
{
    static string dfb_source() // DFB-SOURCE: closure-capture-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: closure-capture-sink

    static Action MakeHandler()
    {
        string captured = dfb_source(); // DFB-WITNESS: closure-capture-store
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

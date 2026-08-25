using System.Collections.Generic;

namespace DataFlowBench;

static class MapIterationPositive
{
    static string dfb_source() // DFB-SOURCE: map-iteration-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: map-iteration-sink

    static void Run()
    {
        Dictionary<string, string> carrier = new Dictionary<string, string>();
        Dictionary<string, string> other = new Dictionary<string, string>();
        other["payload"] = "clean";
        carrier["payload"] = dfb_source(); // DFB-WITNESS: map-iteration-store
        foreach (KeyValuePair<string, string> entry in carrier)
        {
            dfb_sink(entry.Value);
        }
    }
}

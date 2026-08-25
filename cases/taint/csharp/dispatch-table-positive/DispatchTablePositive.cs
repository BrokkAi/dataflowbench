using System;
using System.Collections.Generic;

namespace DataFlowBench;

static class DispatchTablePositive
{
    static string dfb_source() // DFB-SOURCE: dispatch-table-input
    {
        return "tainted";
    }

    static void dfb_sink(string value) { } // DFB-SINK: dispatch-table-sink

    static void Run()
    {
        Dictionary<string, Action<string>> table = new Dictionary<string, Action<string>>();
        table["leak"] = value => // DFB-WITNESS: dispatch-table-entry
        {
            dfb_sink(value);
        };
        table["drop"] = value =>
        {
            dfb_sink("clean");
        };
        string key = "leak";
        Action<string> selected = table[key];
        selected(dfb_source());
    }
}

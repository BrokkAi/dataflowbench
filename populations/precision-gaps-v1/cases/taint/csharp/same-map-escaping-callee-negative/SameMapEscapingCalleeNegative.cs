using System;
using System.Collections.Generic;
public static class SameMapEscapingCalleeNegative {
    static string dfb_source() { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303";
    }
    static void dfb_sink(string value) { Console.WriteLine(value); } // DFB-SINK: issue303-sink
    static void write_source(Dictionary<string, string> values) {
        values["private"] = dfb_source(); // DFB-WITNESS: issue303-callee-store
    }
    static void run(string[] args) {
        var values = new Dictionary<string, string> { ["payload"] = "clean" };
        write_source(values); // DFB-WITNESS: issue303-invoke
        dfb_sink(values["payload"]); // DFB-WITNESS: issue303-read
    }
    public static int Main(string[] args) { run(args); return 0; }
}

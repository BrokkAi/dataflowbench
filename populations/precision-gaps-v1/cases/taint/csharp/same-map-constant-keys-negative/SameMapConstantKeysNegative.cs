using System;
using System.Collections.Generic;
public static class SameMapConstantKeysNegative {
    static string dfb_source() { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303";
    }
    static void dfb_sink(string value) { Console.WriteLine(value); } // DFB-SINK: issue303-sink
    static void run(string[] args) {
        var values = new Dictionary<string, string> { ["payload"] = "clean", ["tainted"] = "clean" };
        values["tainted"] = dfb_source(); // DFB-WITNESS: issue303-store
        dfb_sink(values["payload"]); // DFB-WITNESS: issue303-read
    }
    public static int Main(string[] args) { run(args); return 0; }
}

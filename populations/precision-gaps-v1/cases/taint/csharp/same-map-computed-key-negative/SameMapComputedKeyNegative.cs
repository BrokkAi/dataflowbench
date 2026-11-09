using System;
using System.Collections.Generic;
public static class SameMapComputedKeyNegative {
    static string dfb_source() { // DFB-SOURCE: issue303-source
        return "DFB_SOURCE_303";
    }
    static void dfb_sink(string value) { Console.WriteLine(value); } // DFB-SINK: issue303-sink
    static void run(string[] args) {
        string suffix = args.Length > 0 ? args[0] : "payload";
        string key = "private:" + suffix;
        var values = new Dictionary<string, string> { ["payload"] = "clean" };
        values[key] = dfb_source(); // DFB-WITNESS: issue303-store
        dfb_sink(values["payload"]); // DFB-WITNESS: issue303-read
    }
    public static int Main(string[] args) { run(args); return 0; }
}

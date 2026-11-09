using System;

internal static class ConstantStringSelectorNegative {
    private static string dfb_source() { // DFB-SOURCE: constant-selector-input
        return "source-one";
    }

    private static void dfb_sink(string value) { // DFB-SINK: constant-selector-sink
        Console.WriteLine(value);
    }

    private static void Main() {
        char selector = "ABC"[1];
        string value = selector switch {
            'C' => dfb_source(), // DFB-WITNESS: constant-selector-source-arm
            'B' => "safe",
            _ => "safe",
        };
        dfb_sink(value);
    }
}

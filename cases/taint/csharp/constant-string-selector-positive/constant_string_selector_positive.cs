using System;

internal static class ConstantStringSelectorPositive {
    private static string dfb_source() { // DFB-SOURCE: constant-selector-input
        return "source-one";
    }

    private static void dfb_sink(string value) { // DFB-SINK: constant-selector-sink
        Console.WriteLine(value);
    }

    private static void Main() {
        char selector = "ABC"[2];
        string value;
        switch (selector) {
            case 'C':
                value = dfb_source(); // DFB-WITNESS: constant-selector-source-arm
                break;
            case 'B':
                value = "safe";
                break;
            default:
                value = "safe";
                break;
        }
        dfb_sink(value);
    }
}

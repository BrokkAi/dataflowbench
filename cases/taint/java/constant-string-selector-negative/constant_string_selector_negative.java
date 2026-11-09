final class ConstantStringSelectorNegative {
    private static String dfb_source() {
        return "source-one"; // DFB-SOURCE: constant-selector-input
    }

    private static void dfb_sink(String value) { // DFB-SINK: constant-selector-sink
        System.out.println(value);
    }

    private static void run() {
        String value;
        switch ("ABC".charAt(1)) {
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

    public static void main(String[] args) {
        run();
    }
}

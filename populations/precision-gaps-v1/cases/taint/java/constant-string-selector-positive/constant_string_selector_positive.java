final class ConstantStringSelectorPositive {
    private static String dfb_source() { // DFB-SOURCE: constant-selector-input
        return "source-one";
    }

    private static void dfb_sink(String value) { // DFB-SINK: constant-selector-sink
        System.out.println(value);
    }

    private static void run() {
        String value;
        switch ("ABC".charAt(2)) {
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

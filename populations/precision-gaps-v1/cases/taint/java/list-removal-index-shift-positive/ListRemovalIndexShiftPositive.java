import java.util.ArrayList;
import java.util.List;

final class ListRemovalIndexShiftPositive {
    static int dfb_source() { // DFB-SOURCE: list-removal-index-shift-input
        return Integer.parseInt(System.getenv("DFB_INPUT"));
    }

    static void dfb_sink(int value) { // DFB-SINK: list-removal-index-shift-sink
        System.out.println(value);
    }

    public static void main(String[] args) {
        List<Integer> values = new ArrayList<>();
        values.add(0);
        values.add(dfb_source());
        values.add(9);
        values.remove(0); // DFB-WITNESS: list-removal-index-shift-remove-first
        dfb_sink(values.get(0));
    }
}

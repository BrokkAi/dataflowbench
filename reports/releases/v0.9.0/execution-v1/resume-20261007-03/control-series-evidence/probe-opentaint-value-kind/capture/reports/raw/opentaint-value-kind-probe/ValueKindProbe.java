package probe;

final class ValueKindProbe {
    static String string_src() { return "tainted"; }
    static void string_sink(String value) { }
    static void runString() { string_sink(string_src()); }

    static Object object_src() { return new Object(); }
    static void object_sink(Object value) { }
    static void runObject() { object_sink(object_src()); }

    static int int_src() { return 1; }
    static void int_sink(int value) { }
    static void runInt() { int_sink(int_src()); }

    static Integer boxed_src() { return 1; }
    static void boxed_sink(Integer value) { }
    static void runBoxed() { boxed_sink(boxed_src()); }
}

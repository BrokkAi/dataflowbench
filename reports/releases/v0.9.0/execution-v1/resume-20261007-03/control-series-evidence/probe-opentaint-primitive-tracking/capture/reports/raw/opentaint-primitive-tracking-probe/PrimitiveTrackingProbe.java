package probe;

final class PrimitiveTrackingProbe {
    static String string_src() { return "tainted"; }
    static String string_other() { return "clean"; }
    static void string_sink(String value) { }
    static void runString() { string_sink(string_src()); }
    static void runStringClean() { string_sink(string_other()); }
    static void runStringOverwrite() { String v = string_src(); v = "clean"; string_sink(v); }

    static Object object_src() { return new Object(); }
    static Object object_other() { return new Object(); }
    static void object_sink(Object value) { }
    static void runObject() { object_sink(object_src()); }
    static void runObjectClean() { object_sink(object_other()); }
    static void runObjectOverwrite() { Object v = object_src(); v = new Object(); object_sink(v); }

    static int int_src() { return 1; }
    static int int_other() { return 2; }
    static void int_sink(int value) { }
    static void runInt() { int_sink(int_src()); }
    static void runIntClean() { int_sink(int_other()); }
    static void runIntOverwrite() { int v = int_src(); v = 0; int_sink(v); }

    static Integer boxed_src() { return 1; }
    static Integer boxed_other() { return 2; }
    static void boxed_sink(Integer value) { }
    static void runBoxed() { boxed_sink(boxed_src()); }
    static void runBoxedClean() { boxed_sink(boxed_other()); }
    static void runBoxedOverwrite() { Integer v = boxed_src(); v = 0; boxed_sink(v); }
}

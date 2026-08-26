package dataflowbench.taint;

final class Bridge {
    static String pass(String value) {
        return value;
    }

    static String hold(String value) {
        return value;
    }
}

#include <string>

std::string dfb_source() { // DFB-SOURCE: nested-access-path-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: nested-access-path-sink

struct Leaf {
    std::string value;
    std::string other;
};

struct Middle {
    Leaf c;
};

struct Root {
    Middle b;
};

void run() {
    Root a;
    a.b.c.value = dfb_source(); // DFB-WITNESS: nested-access-path-store
    a.b.c.other = "clean";
    dfb_sink(a.b.c.value);
}

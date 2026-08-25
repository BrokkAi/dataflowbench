#include <string>

std::string dfb_source() { // DFB-SOURCE: recursive-carry-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: recursive-carry-sink

std::string carry(const std::string &value, int depth) {
    if (depth == 0) {
        return value; // DFB-WITNESS: recursive-carry-base
    }
    return carry(value, depth - 1);
}

void run() {
    dfb_sink(carry(dfb_source(), 5));
}

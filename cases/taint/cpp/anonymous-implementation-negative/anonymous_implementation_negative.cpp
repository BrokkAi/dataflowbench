#include <functional>
#include <string>

std::string dfb_source() { // DFB-SOURCE: anonymous-implementation-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: anonymous-implementation-sink

void run() {
    std::function<void(const std::string &)> leaking =
        [](const std::string &value) { dfb_sink(value); };
    std::function<void(const std::string &)> dropping =
        [](const std::string &value) { dfb_sink("clean"); };
    dropping(dfb_source());
}

#include <functional>
#include <string>

std::string dfb_source() { // DFB-SOURCE: closure-capture-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: closure-capture-sink

std::function<void()> make_hook() {
    std::string captured = dfb_source(); // DFB-WITNESS: closure-capture-capture
    std::string clean = "clean";
    return [captured]() { dfb_sink(captured); };
}

void run() {
    std::function<void()> hook = make_hook();
    hook();
}

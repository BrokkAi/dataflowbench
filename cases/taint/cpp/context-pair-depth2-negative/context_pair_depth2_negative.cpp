#include <string>

std::string dfb_source() { // DFB-SOURCE: context-pair-depth2-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: context-pair-depth2-sink

std::string helper(const std::string &value) {
    return value;
}

std::string wrapper(const std::string &value) {
    return helper(value);
}

std::string outer_tainted() {
    return wrapper(dfb_source());
}

std::string outer_clean() {
    return wrapper("clean");
}

void run() {
    std::string tainted = outer_tainted();
    std::string clean = outer_clean();
    dfb_sink(clean);
}

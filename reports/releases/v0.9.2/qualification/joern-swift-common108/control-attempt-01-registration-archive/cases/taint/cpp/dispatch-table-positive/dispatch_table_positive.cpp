#include <functional>
#include <map>
#include <string>

std::string dfb_source() { // DFB-SOURCE: dispatch-table-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: dispatch-table-sink

void leak(const std::string &value) {
    dfb_sink(value);
}

void drop(const std::string &value) {
    dfb_sink("clean");
}

void run() {
    std::map<std::string, std::function<void(const std::string &)>> table; // DFB-WITNESS: dispatch-table-build
    table["leak"] = leak;
    table["drop"] = drop;
    std::string key = "leak";
    table[key](dfb_source());
}

#include <map>
#include <string>

std::string dfb_source() { // DFB-SOURCE: computed-property-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: computed-property-sink

void run() {
    std::map<std::string, std::string> holder;
    holder["payload"] = dfb_source();
    holder["other"] = "clean";
    dfb_sink(holder["other"]);
}

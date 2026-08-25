#include <map>
#include <string>

std::string dfb_source() { // DFB-SOURCE: computed-property-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: computed-property-sink

void run() {
    std::map<std::string, std::string> holder;
    std::string key = "payload";
    holder[key] = dfb_source(); // DFB-WITNESS: computed-property-store
    dfb_sink(holder[key]);
}

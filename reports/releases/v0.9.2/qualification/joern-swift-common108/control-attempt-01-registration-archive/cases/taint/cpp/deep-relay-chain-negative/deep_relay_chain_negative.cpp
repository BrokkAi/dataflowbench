#include <string>

std::string dfb_source() { // DFB-SOURCE: deep-relay-chain-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: deep-relay-chain-sink

std::string relay6(const std::string &value) {
    return value;
}

std::string relay5(const std::string &value) {
    return relay6(value);
}

std::string relay4(const std::string &value) {
    return relay5(value);
}

std::string relay3(const std::string &value) {
    return relay4(value);
}

std::string relay2(const std::string &value) {
    return relay3(value);
}

std::string relay1(const std::string &value) {
    return relay2(value);
}

void run() {
    std::string tainted = dfb_source();
    dfb_sink(relay1("clean"));
}

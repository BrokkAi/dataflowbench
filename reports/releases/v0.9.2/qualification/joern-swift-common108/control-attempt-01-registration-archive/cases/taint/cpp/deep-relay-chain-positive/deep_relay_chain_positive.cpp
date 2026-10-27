#include <string>

std::string dfb_source() { // DFB-SOURCE: deep-relay-chain-input
    return "tainted";
}

void dfb_sink(const std::string &value) {} // DFB-SINK: deep-relay-chain-sink

std::string relay6(const std::string &value) { // DFB-WITNESS: deep-relay-chain-hop6
    return value;
}

std::string relay5(const std::string &value) { // DFB-WITNESS: deep-relay-chain-hop5
    return relay6(value);
}

std::string relay4(const std::string &value) { // DFB-WITNESS: deep-relay-chain-hop4
    return relay5(value);
}

std::string relay3(const std::string &value) { // DFB-WITNESS: deep-relay-chain-hop3
    return relay4(value);
}

std::string relay2(const std::string &value) { // DFB-WITNESS: deep-relay-chain-hop2
    return relay3(value);
}

std::string relay1(const std::string &value) { // DFB-WITNESS: deep-relay-chain-hop1
    return relay2(value);
}

void run() {
    std::string tainted = dfb_source();
    dfb_sink(relay1(tainted));
}

int dfb_source(void) { // DFB-SOURCE: deep-relay-chain-input
    return 1;
}

int relay6(int value) { // DFB-WITNESS: deep-relay-chain-hop6
    return value;
}

int relay5(int value) { // DFB-WITNESS: deep-relay-chain-hop5
    return relay6(value);
}

int relay4(int value) { // DFB-WITNESS: deep-relay-chain-hop4
    return relay5(value);
}

int relay3(int value) { // DFB-WITNESS: deep-relay-chain-hop3
    return relay4(value);
}

int relay2(int value) { // DFB-WITNESS: deep-relay-chain-hop2
    return relay3(value);
}

int relay1(int value) { // DFB-WITNESS: deep-relay-chain-hop1
    return relay2(value);
}

void dfb_sink(int value) {} // DFB-SINK: deep-relay-chain-sink

void run(void) {
    int tainted = dfb_source();
    dfb_sink(relay1(0));
}

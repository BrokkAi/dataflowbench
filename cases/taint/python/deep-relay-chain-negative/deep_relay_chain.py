def dfb_source():  # DFB-SOURCE: deep-relay-chain-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: deep-relay-chain-sink
    pass


def relay1(value):  # DFB-WITNESS: deep-relay-chain-hop1
    return relay2(value)


def relay2(value):  # DFB-WITNESS: deep-relay-chain-hop2
    return relay3(value)


def relay3(value):  # DFB-WITNESS: deep-relay-chain-hop3
    return relay4(value)


def relay4(value):  # DFB-WITNESS: deep-relay-chain-hop4
    return relay5(value)


def relay5(value):  # DFB-WITNESS: deep-relay-chain-hop5
    return relay6(value)


def relay6(value):  # DFB-WITNESS: deep-relay-chain-hop6
    return value


def run():
    tainted = dfb_source()
    dfb_sink(relay1("clean"))

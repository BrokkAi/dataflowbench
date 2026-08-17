def dfb_source():  # DFB-SOURCE: return-one-hop-negative-input
    return "tainted"


def relay(value):  # DFB-WITNESS: return-one-hop-negative-relay
    return value


def dfb_sink(value):  # DFB-SINK: return-one-hop-negative-sink
    pass


def run():
    result = relay(dfb_source())
    dfb_sink("clean")

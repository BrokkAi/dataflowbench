def dfb_source():  # DFB-SOURCE: call-context-input
    return "tainted"


def relay(value):  # DFB-WITNESS: call-context-relay
    return value


def dfb_sink(value):  # DFB-SINK: call-context-sink
    pass


def run():
    tainted = relay(dfb_source())
    clean = relay("clean")
    dfb_sink(clean)

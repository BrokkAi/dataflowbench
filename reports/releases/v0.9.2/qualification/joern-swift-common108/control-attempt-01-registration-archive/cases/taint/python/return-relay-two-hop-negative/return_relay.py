def dfb_source():  # DFB-SOURCE: return-two-hop-negative-input
    return "tainted"


def first_relay(value):  # DFB-WITNESS: return-two-hop-negative-first
    return value


def second_relay(value):  # DFB-WITNESS: return-two-hop-negative-second
    return first_relay(value)


def dfb_sink(value):  # DFB-SINK: return-two-hop-negative-sink
    pass


def run():
    result = second_relay(dfb_source())
    dfb_sink("clean")

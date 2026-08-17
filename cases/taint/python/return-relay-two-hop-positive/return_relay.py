def dfb_source():  # DFB-SOURCE: return-two-hop-input
    return "tainted"


def first_relay(value):  # DFB-WITNESS: return-two-hop-first
    return value


def second_relay(value):  # DFB-WITNESS: return-two-hop-second
    return first_relay(value)


def dfb_sink(value):  # DFB-SINK: return-two-hop-sink
    pass


def run():
    result = second_relay(dfb_source())
    dfb_sink(result)

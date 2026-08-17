def dfb_source():  # DFB-SOURCE: local-chain-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: local-chain-sink
    pass


def run():
    first = dfb_source()
    second = first  # DFB-WITNESS: local-chain-second
    third = second  # DFB-WITNESS: local-chain-third
    dfb_sink(third)

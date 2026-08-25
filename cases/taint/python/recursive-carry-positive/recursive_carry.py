def dfb_source():  # DFB-SOURCE: recursive-carry-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: recursive-carry-sink
    pass


def carry(value, depth):  # DFB-WITNESS: recursive-carry-step
    if depth == 0:
        return value
    return carry(value, depth - 1)


def run():
    dfb_sink(carry(dfb_source(), 5))

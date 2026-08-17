def dfb_source():  # DFB-SOURCE: expression-negative-input
    return 1


def dfb_sink(value):  # DFB-SINK: expression-negative-sink
    pass


def run():
    value = dfb_source()
    computed = (value * 3) + 7  # DFB-WITNESS: expression-negative-computed
    dfb_sink(7)

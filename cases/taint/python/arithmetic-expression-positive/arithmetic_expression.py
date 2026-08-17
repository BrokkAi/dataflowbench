def dfb_source():  # DFB-SOURCE: expression-input
    return 1


def dfb_sink(value):  # DFB-SINK: expression-sink
    pass


def run():
    value = dfb_source()
    computed = (value * 3) + 7  # DFB-WITNESS: expression-computed
    dfb_sink(computed)

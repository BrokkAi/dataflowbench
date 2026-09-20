def dfb_source():  # DFB-SOURCE: trivial-overhead-input
    return 1


def dfb_sink(value):  # DFB-SINK: trivial-overhead-sink
    pass


def run():
    dfb_source()
    dfb_sink(0)

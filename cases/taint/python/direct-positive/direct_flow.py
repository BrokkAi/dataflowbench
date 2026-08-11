def dfb_source():  # DFB-SOURCE: direct-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: direct-sink
    pass


def run():
    dfb_sink(dfb_source())


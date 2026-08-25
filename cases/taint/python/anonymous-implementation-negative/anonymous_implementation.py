def dfb_source():  # DFB-SOURCE: anonymous-implementation-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: anonymous-implementation-sink
    pass


def run():
    leak = lambda value: dfb_sink(value)  # DFB-WITNESS: anonymous-implementation-bind
    drop = lambda value: dfb_sink("clean")
    drop(dfb_source())

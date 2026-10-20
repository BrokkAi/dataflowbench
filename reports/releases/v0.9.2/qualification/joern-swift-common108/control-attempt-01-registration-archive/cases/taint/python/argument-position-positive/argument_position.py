def dfb_source():  # DFB-SOURCE: argument-position-input
    return "tainted"


def choose_first(first, second):  # DFB-WITNESS: argument-position-first
    return first


def dfb_sink(value):  # DFB-SINK: argument-position-sink
    pass


def run():
    result = choose_first(dfb_source(), "clean")
    dfb_sink(result)

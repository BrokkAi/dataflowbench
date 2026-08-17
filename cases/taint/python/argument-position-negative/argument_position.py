def dfb_source():  # DFB-SOURCE: argument-position-negative-input
    return "tainted"


def choose_first(first, second):  # DFB-WITNESS: argument-position-negative-first
    return first


def dfb_sink(value):  # DFB-SINK: argument-position-negative-sink
    pass


def run():
    result = choose_first("clean", dfb_source())
    dfb_sink(result)

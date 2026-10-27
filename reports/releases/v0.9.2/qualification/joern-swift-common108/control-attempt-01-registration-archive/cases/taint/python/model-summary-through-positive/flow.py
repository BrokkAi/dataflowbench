from bridge import hold, pass_through


def dfb_source():  # DFB-SOURCE: model-summary-through-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-summary-through-sink
    pass


def run():
    dfb_sink(pass_through(dfb_source()))


def unused():
    return (hold, pass_through)

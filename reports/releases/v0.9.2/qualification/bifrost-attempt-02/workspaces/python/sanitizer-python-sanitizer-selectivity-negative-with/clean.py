def scrub(value):
    return value


def sanitize(value):
    return value


def dfb_source():  # DFB-SOURCE: model-sanitizer-selectivity-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-sanitizer-selectivity-sink
    pass


def run():
    dfb_sink(scrub(dfb_source()))

def fetch_remote():  # DFB-SOURCE: model-declared-source-input
    return "r"


def fetch_local():
    return "l"


def dfb_sink(value):  # DFB-SINK: model-declared-source-sink
    pass


def run():
    dfb_sink(fetch_local())

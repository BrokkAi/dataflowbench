def dfb_sink(value):  # DFB-SINK: model-entrypoint-selectivity-sink
    pass


def on_declared(payload):  # DFB-SOURCE: model-entrypoint-selectivity-input
    dfb_sink("clean")


def on_undeclared(payload):
    dfb_sink(payload)

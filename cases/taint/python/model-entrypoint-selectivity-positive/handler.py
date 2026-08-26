def dfb_sink(value):  # DFB-SINK: model-entrypoint-selectivity-sink
    pass


def on_declared(payload):  # DFB-SOURCE: model-entrypoint-selectivity-input
    dfb_sink(payload)


def on_undeclared(payload):
    dfb_sink("clean")

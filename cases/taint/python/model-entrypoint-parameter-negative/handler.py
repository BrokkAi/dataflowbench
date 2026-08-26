def dfb_sink(value):  # DFB-SINK: model-entrypoint-parameter-sink
    pass


def on_request(payload):  # DFB-SOURCE: model-entrypoint-parameter-input
    dfb_sink("clean")


def on_ignored(payload):
    dfb_sink(payload)

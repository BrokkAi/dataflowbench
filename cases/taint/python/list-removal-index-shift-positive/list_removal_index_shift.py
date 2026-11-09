import os


def dfb_source():  # DFB-SOURCE: list-removal-index-shift-input
    return os.environ["DFB_INPUT"]


def dfb_sink(value):  # DFB-SINK: list-removal-index-shift-sink
    print(value)


values = []
values.append("safe")
values.append(dfb_source())
values.append("more-safe")
values.pop(0)  # DFB-WITNESS: list-removal-index-shift-remove-first
dfb_sink(values[0])

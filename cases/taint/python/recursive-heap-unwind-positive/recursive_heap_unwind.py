class FlowBox:
    def __init__(self, value):
        self.value = value


def dfb_source():  # DFB-SOURCE: recursive-heap-unwind-input
    return 7


def dfb_sink(value):  # DFB-SINK: recursive-heap-unwind-sink
    pass


def walk(box, value, depth):
    if depth == 0:
        box.value = value  # DFB-WITNESS: recursive-heap-unwind-base
        return
    walk(box, value, depth - 1)  # DFB-WITNESS: recursive-heap-unwind-transfer
    box.value = box.value + 1  # DFB-WITNESS: recursive-heap-unwind-compose


def run():
    box = FlowBox(0)
    walk(box, dfb_source(), 3)
    dfb_sink(box.value)

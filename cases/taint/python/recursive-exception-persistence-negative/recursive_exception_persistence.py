class FlowException(Exception):
    pass


class FlowBox:
    def __init__(self, value):
        self.value = value


def dfb_source():  # DFB-SOURCE: recursive-exception-persistence-input
    return 7


def dfb_sink(value):  # DFB-SINK: recursive-exception-persistence-sink
    pass


def walk(box, value, depth):
    if depth == 0:
        box.value = value  # DFB-WITNESS: recursive-exception-persistence-base
        box.value = 0  # DFB-KILL: recursive-exception-persistence-base-overwrite
        raise FlowException("recursive exceptional exit")  # DFB-WITNESS: recursive-exception-persistence-throw
    walk(box, value, depth - 1)  # DFB-WITNESS: recursive-exception-persistence-transfer


def run():
    box = FlowBox(0)
    try:
        walk(box, dfb_source(), 3)
    except FlowException:
        result = box.value + 1  # DFB-WITNESS: recursive-exception-persistence-compose
        dfb_sink(result)

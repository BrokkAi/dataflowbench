class FlowException(Exception):
    pass


class FlowBox:
    def __init__(self, value):
        self.value = value


def dfb_source():  # DFB-SOURCE: exception-persistence-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: exception-persistence-sink
    pass


def store_and_throw(box, value):
    box.value = value  # DFB-WITNESS: exception-persistence-store
    box.value = "clean"  # DFB-WITNESS: exception-persistence-kill
    raise FlowException("exceptional exit")  # DFB-WITNESS: exception-persistence-throw


def recover(box, value):
    try:
        store_and_throw(box, value)
        return "unreachable"
    except FlowException:
        return box.value  # DFB-WITNESS: exception-persistence-recovery


def run():
    box = FlowBox("seed")
    dfb_sink(recover(box, dfb_source()))

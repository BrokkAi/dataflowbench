class FlowException(Exception):
    pass


def dfb_source():  # DFB-SOURCE: exception-catch-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: exception-catch-sink
    pass


def run():
    try:
        flow = FlowException()
        flow.value = dfb_source()
        raise flow  # DFB-WITNESS: exception-catch-throw
    except FlowException as caught:
        dfb_sink(caught.value)

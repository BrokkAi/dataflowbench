def dfb_source():  # DFB-SOURCE: closure-capture-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: closure-capture-sink
    pass


def make_reporter():
    tainted = dfb_source()  # DFB-WITNESS: closure-capture-bind
    captured = "clean"

    def reporter():
        dfb_sink(captured)

    return reporter


def run():
    reporter = make_reporter()
    reporter()

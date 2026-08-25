def dfb_source():  # DFB-SOURCE: reflective-invocation-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: reflective-invocation-sink
    pass


class Target:
    def leak(self, value):
        dfb_sink(value)

    def drop(self, value):
        dfb_sink("clean")


def run():
    target = Target()
    name = "leak"
    method = getattr(target, name)  # DFB-WITNESS: reflective-invocation-resolve
    method(dfb_source())

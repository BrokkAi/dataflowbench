class _Impl:
    @staticmethod
    def second(first, second):
        return second


_impl = _Impl()


def select(first, second):
    name = "second"
    return getattr(_impl, name)(first, second)


def dfb_source():  # DFB-SOURCE: model-propagator-position-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-propagator-position-sink
    pass


def run():
    dfb_sink(select("clean", dfb_source()))

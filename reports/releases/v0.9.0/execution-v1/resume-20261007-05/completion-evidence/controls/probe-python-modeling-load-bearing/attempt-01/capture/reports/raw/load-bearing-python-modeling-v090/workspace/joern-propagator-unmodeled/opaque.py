class _Impl:
    @staticmethod
    def identity(value):
        return value


_impl = _Impl()


def carry(value):
    name = "identity"
    return getattr(_impl, name)(value)


def block(value):
    name = "identity"
    return getattr(_impl, name)(value)


def dfb_source():  # DFB-SOURCE: model-opaque-propagator-input
    return "tainted"


def dfb_sink(value):  # DFB-SINK: model-opaque-propagator-sink
    pass


def run():
    dfb_sink(carry(dfb_source()))

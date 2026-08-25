def dfb_source # DFB-SOURCE: anonymous-implementation-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: anonymous-implementation-sink
end

def run
  leak = Class.new do # DFB-WITNESS: anonymous-implementation-bind
    def handle(value)
      dfb_sink(value)
    end
  end.new
  drop = Class.new do
    def handle(value)
      dfb_sink("clean")
    end
  end.new
  drop.handle(dfb_source)
end

def dfb_source # DFB-SOURCE: closure-capture-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: closure-capture-sink
end

def make_reporter
  tainted = dfb_source # DFB-WITNESS: closure-capture-bind
  captured = "clean"
  -> { dfb_sink(captured) }
end

def run
  reporter = make_reporter
  reporter.call
end

def dfb_source # DFB-SOURCE: call-context-input
  "tainted"
end

def relay(value) # DFB-WITNESS: call-context-relay
  value
end

def dfb_sink(value) # DFB-SINK: call-context-sink
end

def run
  tainted = relay(dfb_source)
  clean = relay("clean")
  dfb_sink(clean)
end

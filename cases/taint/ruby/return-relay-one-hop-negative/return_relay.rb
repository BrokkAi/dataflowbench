def dfb_source # DFB-SOURCE: return-one-hop-negative-input
  "tainted"
end

def relay(value) # DFB-WITNESS: return-one-hop-negative-relay
  value
end

def dfb_sink(value) # DFB-SINK: return-one-hop-negative-sink
end

def run
  result = relay(dfb_source)
  dfb_sink("clean")
end

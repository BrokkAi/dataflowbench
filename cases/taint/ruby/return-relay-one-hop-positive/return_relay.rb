def dfb_source # DFB-SOURCE: return-one-hop-input
  "tainted"
end

def relay(value) # DFB-WITNESS: return-one-hop-relay
  value
end

def dfb_sink(value) # DFB-SINK: return-one-hop-sink
end

def run
  result = relay(dfb_source)
  dfb_sink(result)
end

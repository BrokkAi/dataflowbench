def dfb_source # DFB-SOURCE: return-two-hop-negative-input
  "tainted"
end

def first_relay(value) # DFB-WITNESS: return-two-hop-negative-first
  value
end

def second_relay(value) # DFB-WITNESS: return-two-hop-negative-second
  first_relay(value)
end

def dfb_sink(value) # DFB-SINK: return-two-hop-negative-sink
end

def run
  result = second_relay(dfb_source)
  dfb_sink("clean")
end

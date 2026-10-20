def dfb_source # DFB-SOURCE: local-chain-negative-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: local-chain-negative-sink
end

def run
  first = dfb_source
  second = first # DFB-WITNESS: local-chain-negative-second
  third = second # DFB-WITNESS: local-chain-negative-third
  dfb_sink("clean")
end

def dfb_source # DFB-SOURCE: local-chain-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: local-chain-sink
end

def run
  first = dfb_source
  second = first # DFB-WITNESS: local-chain-second
  third = second # DFB-WITNESS: local-chain-third
  dfb_sink(third)
end

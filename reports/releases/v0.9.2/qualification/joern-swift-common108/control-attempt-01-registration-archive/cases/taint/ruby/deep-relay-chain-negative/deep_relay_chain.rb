def dfb_source # DFB-SOURCE: deep-relay-chain-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: deep-relay-chain-sink
end

def relay1(value) # DFB-WITNESS: deep-relay-chain-hop1
  relay2(value)
end

def relay2(value) # DFB-WITNESS: deep-relay-chain-hop2
  relay3(value)
end

def relay3(value) # DFB-WITNESS: deep-relay-chain-hop3
  relay4(value)
end

def relay4(value) # DFB-WITNESS: deep-relay-chain-hop4
  relay5(value)
end

def relay5(value) # DFB-WITNESS: deep-relay-chain-hop5
  relay6(value)
end

def relay6(value) # DFB-WITNESS: deep-relay-chain-hop6
  value
end

def run
  tainted = dfb_source
  dfb_sink(relay1("clean"))
end

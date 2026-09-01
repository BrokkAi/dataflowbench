def dfb_source # DFB-SOURCE: trivial-overhead-input
  1
end

def dfb_sink(value) # DFB-SINK: trivial-overhead-sink
end

def run
  dfb_source
  dfb_sink(0)
end

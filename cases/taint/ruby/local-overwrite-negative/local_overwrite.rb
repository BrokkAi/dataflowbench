def dfb_source # DFB-SOURCE: local-overwrite-input
  "tainted"
end

def dfb_sink(value) # DFB-SINK: local-overwrite-sink
end

def run
  value = dfb_source
  value = "clean" # DFB-KILL: local-overwrite-clean
  dfb_sink(value)
end
